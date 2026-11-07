import tkinter as tk

class CalibrationGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("EOG Calibration Protocol")
        
        # Make full screen, black background
        self.root.attributes('-fullscreen', True)
        self.root.configure(bg='black')
        self.root.bind("<Escape>", lambda e: self.root.quit()) # Press Esc to exit
        
        # Get screen dimensions
        self.width = self.root.winfo_screenwidth()
        self.height = self.root.winfo_screenheight()
        
        # Create a canvas to draw the dot and text
        self.canvas = tk.Canvas(self.root, width=self.width, height=self.height, 
                                bg='black', highlightthickness=0)
        self.canvas.pack()
        
        # Dot properties
        self.dot_radius = 40
        self.hold_time_ms = 5000 # 5 seconds per position
        
        # Define the dot coordinates for the extreme edges of your laptop screen
        margin = 100
        cx, cy = self.width / 2, self.height / 2
        
        self.positions = [
            ("CENTER (Baseline)", cx, cy),
            ("RIGHT", self.width - margin, cy),
            ("CENTER (Recovery)", cx, cy),
            ("LEFT", margin, cy),
            ("CENTER (Recovery)", cx, cy),
            ("UP", cx, margin),
            ("CENTER (Recovery)", cx, cy),
            ("DOWN", cx, self.height - margin),
            ("CENTER (Final)", cx, cy)
        ]
        
        self.current_step = 0
        
        # Start Screen
        self.instruction_text = self.canvas.create_text(
            cx, cy, 
            text="Press SPACE to start calibration.\nKeep your head perfectly still.\nFollow the green dot with your eyes.", 
            fill="white", font=("Arial", 32, "bold"), justify="center"
        )
        self.root.bind("<space>", self.start_protocol)

    def start_protocol(self, event=None):
        self.root.unbind("<space>") # Prevent multiple triggers
        self.canvas.delete(self.instruction_text)
        
        # Start ANT recording simultaneously, then trigger the sequence
        self.run_step()

    def run_step(self):
        self.canvas.delete("all")
        
        if self.current_step < len(self.positions):
            label, x, y = self.positions[self.current_step]
            
            # Draw the target dot
            self.canvas.create_oval(
                x - self.dot_radius, y - self.dot_radius,
                x + self.dot_radius, y + self.dot_radius,
                fill="lime green", outline="white", width=3
            )
            
            # Draw text instruction in the center of the screen
            self.canvas.create_text(
                self.width / 2, self.height / 2,
                text=f"Look {label}\nDo not move your head.\nHold for 5 seconds...",
                fill="white", font=("Arial", 28), justify="center"
            )
            
            self.current_step += 1
            # Schedule the next step after 5 seconds
            self.root.after(self.hold_time_ms, self.run_step)
            
        else:
            # End of protocol
            self.canvas.create_text(
                self.width / 2, self.height / 2,
                text="Calibration Complete.\nYou can stop the ANT recording.\nPress ESC to exit.",
                fill="cyan", font=("Arial", 36, "bold"), justify="center"
            )

if __name__ == "__main__":
    root = tk.Tk()
    app = CalibrationGUI(root)
    root.mainloop()