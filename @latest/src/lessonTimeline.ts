export type Direction = 'LEFT' | 'RIGHT' | 'CENTER'
export type Interval = { direction: Direction; start: number; end: number }

export function parseTimings(csv: string): Interval[] {
  const intervals = csv.trim().split(/\r?\n/).slice(1).map((row) => {
    const [direction, timestamp, duration] = row.split(',').map((value) => value.trim())
    const start = Number(timestamp) - 8
    const seconds = Number(duration)
    if (!['LEFT', 'RIGHT', 'CENTER'].includes(direction) ||
        !Number.isFinite(start) || !Number.isFinite(seconds) || start < 0 || seconds <= 0) {
      throw new Error(`Invalid timing row: ${row}`)
    }
    return { direction: direction as Direction, start, end: start + seconds }
  })
  if (!intervals.length || intervals.some((interval, index) =>
    index > 0 && interval.start < intervals[index - 1].end)) {
    throw new Error('Timings must contain non-overlapping intervals in timestamp order.')
  }
  return intervals
}

// Derive progress from absolute elapsed time so delayed frames cannot skip answers
// or shorten a direction's hold on the question that it belongs to.
export function getPlayback(intervals: Interval[], elapsed: number, correctSides: Direction[]) {
  let questionIndex = 0
  for (const interval of intervals) {
    if (elapsed < interval.end) break
    if (interval.direction !== 'CENTER' && interval.direction === correctSides[questionIndex]) {
      questionIndex += 1
    }
  }
  const complete = questionIndex === correctSides.length
  return {
    questionIndex,
    complete,
    active: complete ? undefined : intervals.find((interval) =>
      elapsed >= interval.start && elapsed < interval.end),
    finished: elapsed >= intervals[intervals.length - 1].end,
  }
}
