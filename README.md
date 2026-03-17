# Checkmate - A Senior Design Project at Syracuse University

### Authors:
- Zachary Starr
- Zane Obiofuma

This repo strictly just contains the software used in this project. The hardware: the robotic arm, circuit w/ the microcontroller, motor drivers, Arduinos, etc. are not 
showcased in this repo. Below is a list of all the hardware/software components we used in this project.

#### Hardware used:
- Arduino Leonardo
- Arduino M4
- Adafruit 16-Channel PCA9865 Motor Driver
- 6 Servo Motors
- 1080p Video Camera
- 2 Buttons
- 6V Power Supply

#### Software used:
- Stockfish --> Open Source
- Python --> Open Source

#### Key Technologies:
- Stockfish: AI chess engine which analyzes chess positions using FEN string to calculate the best possible moves.
- Computer Vision: Utilizing Python’s OpenCV library, the camera processes the board at the start of a game and captures an image of the updated board after every move. 
  Works in tandem to update the FEN string for Stockfish.
- Inverse Kinematics: Developed an algebraic coordinate system for the board with each individual tile’s position and the arm’s defined “home” positions mapped. Python is
  used to map the system into a cartesian coordinate system so the arm’s motors can receive the correct angles to reach each individual tile through inverse kinematic
  equations for each joint.

This link will show you how to download Stockfish onto your local machine: https://stockfishchess.org/download/
Just pick your OS and follow the installation steps as required.


### Reference-

<img width="919" height="607" alt="image" src="https://github.com/user-attachments/assets/bd32a0e4-6d4b-47f7-8b15-58ccd2db5328" />
