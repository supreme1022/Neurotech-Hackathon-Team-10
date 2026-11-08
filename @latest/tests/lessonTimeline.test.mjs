import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import test from 'node:test'
import { getPlayback, parseTimings } from '../src/lessonTimeline.ts'

const intervals = parseTimings(readFileSync(new URL('../../timings.csv', import.meta.url), 'utf8'))
const answers = ['LEFT', 'RIGHT', 'LEFT', 'RIGHT', 'LEFT']
const at = (seconds) => getPlayback(intervals, seconds, answers)

test('timestamp 8 starts immediately centered and direction boundaries are exact', () => {
  assert.equal(at(0).active.direction, 'CENTER')
  assert.equal(at(5.999).active.direction, 'CENTER')
  assert.equal(at(6).active.direction, 'RIGHT')
  assert.equal(at(15.999).active.direction, 'RIGHT')
  assert.equal(at(16).active.direction, 'CENTER')
  assert.equal(at(22).active.direction, 'LEFT')
})

test('incorrect holds do not advance; correct holds advance only at their end', () => {
  assert.equal(at(16).questionIndex, 0)
  assert.equal(at(31.999).questionIndex, 0)
  assert.equal(at(32).questionIndex, 1)
  assert.equal(at(32).active.direction, 'CENTER')
})

test('playback stops after 38 seconds without repeating or completing five questions', () => {
  assert.equal(at(37.999).finished, false)
  for (const seconds of [38, 100, 1000]) {
    assert.equal(at(seconds).finished, true)
    assert.equal(at(seconds).active, undefined)
    assert.equal(at(seconds).questionIndex, 1)
    assert.equal(at(seconds).complete, false)
  }
  assert.equal(at(0).questionIndex, 0)
})

test('delayed frames account for all finished holds against the appropriate question', () => {
  const playback = getPlayback(intervals, 38, ['RIGHT', 'LEFT'])
  assert.equal(playback.questionIndex, 2)
  assert.equal(playback.complete, true)
  assert.equal(playback.active, undefined)
})

test('invalid or overlapping intervals are rejected', () => {
  assert.throws(() => parseTimings('direction,timestamp,duration\nUP,8,6'))
  assert.throws(() => parseTimings('direction,timestamp,duration\nLEFT,8,-1'))
  assert.throws(() => parseTimings('direction,timestamp,duration\nLEFT,8,6\nRIGHT,10,5'))
})
