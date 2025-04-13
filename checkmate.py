import serial
import cv2
import time
import os
import numpy as np
import cv2.aruco as aruco
import copy
import chess
import chess.engine
from array import array
import pyttsx3

engine = pyttsx3.init()

from sympy.codegen.ast import break_
from tomlkit import string

# import chess.engine
# from array import array

stockfish_path = "C:/Users/zobio/Downloads/stockfish-windows-x86-64-avx2 (1)/stockfish/stockfish-windows-x86-64-avx2.exe"

log_moves = []

arduino = serial.Serial(port='COM5', baudrate=9600, timeout=1)
leo = serial.Serial('COM7', 9600, timeout=1)


cap = cv2.VideoCapture(0)

folder_path = os.path.join("board_img")
print(folder_path)
position_dict = {}

dictionary = aruco.getPredefinedDictionary(aruco.DICT_5X5_50)
parameters = aruco.DetectorParameters()
detector = aruco.ArucoDetector(dictionary, parameters)

w_turn = True
white = True

board2 = chess.Board()

fen_1 = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR"
fen_2 = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR"

# p_m = ""
p_move = ""
message = ""

count = 0
count_1s = 32
global defult_dict

old = True

marker_labels = {

    # white team
    0: "P1", 1: "P2", 2: "P3", 3: "P4", 4: "P5", 5: "P6",
    6: "P7", 7: "P8", 8: "R1", 9: "R2", 10: "N1", 11: "N2",
    12: "B1", 13: "B2", 14: "Q1", 15: "K1",

    # Black team (robot)
    16: "p1", 17: "p2", 18: "p3", 19: "p4", 20: "p5", 21: "p6",
    22: "p7", 23: "p8", 24: "r1", 25: "r2", 26: "n1", 27: "n2",
    28: "b1", 29: "b2", 30: "q1", 31: "k1"

}



def castling_happened(fen_before, fen_after):
    board_before = chess.Board(fen_before)
    board_after = chess.Board(fen_after)

    yes = True

    king_moves = {
        "e1g1": "White kingside",
        "e1c1": "White queenside",
        # "Ke8g8": "Black kingside",
        # "e8c8": "Black queenside"
    }

    move = board_before.board_fen() + " -> " + board_after.board_fen()

    for uci, label in king_moves.items():
        move_obj = chess.Move.from_uci(uci)
        if board_before.is_legal(move_obj):
            board_before.push(move_obj)
            if board_before.board_fen() == board_after.board_fen():
                uci = f"K{uci}"
                return uci
            board_before.pop()
    return None


def check_if_piece_was_taken(fen_before, move):
    global  board2
    board2 = chess.Board(fen_before)
    captured_piece = board2.piece_at(move.to_square)  # Check if a piece was on the destination
    board2.push(move)  # Make the move

    if captured_piece is not None:  # If a piece was there, it was captured
        return True, captured_piece.symbol()
    return False, None


def analyze_moves_with_stockfish(moves):
    global  board2
    board2 = chess.Board()
    captures = 0

    with chess.engine.SimpleEngine.popen_uci(stockfish_path) as engine:
        for move_uci in moves:
            move = chess.Move.from_uci(move_uci)
            was_taken, piece = check_if_piece_was_taken(board2.fen(), move)
            if was_taken:
                captures += 1
                # print(f"Move {move_uci}: Piece '{piece}' was taken.")
        # print(f"Total pieces taken: {captures}")
    return captures, was_taken



def board_to_fen(board):
    fen = ''
    for row in board:
        empty_count = 0
        for square in row:
            if square == '1':
                empty_count += 1
            else:
                if empty_count > 0:
                    fen += str(empty_count)
                    empty_count = 0
                fen += square
        if empty_count > 0:
            fen += str(empty_count)
        fen += '/'

    return fen[:-1]  # Remove the last '/' to match FEN format


def update_fen(board, is_white_turn):
    global fen_1, fen_2
    new_fen = board_to_fen(board)
    if is_white_turn:
        fen_1 = new_fen

    else:
        fen_2 = new_fen

    if count >= 0:
        result = castling_happened(fen_2,fen_1)
        origin, destination, piece, captured_piece = find_move(fen_2, fen_1)

        # Convert the coordinates to algebraic notation
        origin_square = coordinates_to_algebraic(origin[0], origin[1])
        destination_square = coordinates_to_algebraic(destination[0], destination[1])

        # Print the move in algebraic notation
        if result:
            p_move = result
        else:
            p_move = f"{piece}{origin_square}{destination_square}"
        if captured_piece:
            p_move =  f"{piece}{origin_square}{destination_square}"

        # if check_castle_move== "Ke1d1":
        #     p_move = f"Ke1c1"
        # elif check_castle_move== "Kh1d1":
        #     p_move = f"Ke1g1"

        print("\nplayers move: ",p_move)
        print("\n")
        # print(f"Move: {piece}{origin_square}{destination_square}")
        return p_move, captured_piece
    # print("FEN 1:", fen_1)
    # print("FEN 2:", fen_2)


def calib(frame):
    global defult_dict
    global x_diff
    image = frame
    gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray_image, (5, 5), 0)
    ret, corners = cv2.findChessboardCorners(gray_image, (7, 7))
    files = "ABCDEFGH"
    ranks = "12345678"

    edges = cv2.Canny(blurred, 50, 150)

    # Find contours in the edge-detected image
    contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    # Find the largest contour, which should correspond to the chessboard's outer edge
    largest_contour = max(contours, key=cv2.contourArea)

    # Approximate the contour to a polygon
    epsilon = 0.1 * cv2.arcLength(largest_contour, True)
    approx = cv2.approxPolyDP(largest_contour, epsilon, True)

    # Ensure the approximated contour has four points
    if len(approx) == 4:
        # Draw the outline of the chessboard
        cv2.drawContours(image, [approx], -1, (0, 255, 0), 2)
    if ret:
        # Draw the chessboard corners
        image = cv2.drawChessboardCorners(image, (7, 7), corners, ret)

        for y, x in corners[0]:
            # print (c)
            x_diff1 = x

        for y, x in corners[1]:
            # print (c)
            x_diff2 = x

        x_diff = x_diff2 - x_diff1  # the x space between the points
        # print(x_diff)

        y2 = 0
        y1 = 0
        count = 0

        # -----------------------------GET THE Y DIFF FIRST-----------------------------------
        for i, corner in enumerate(corners):
            # Calculate file and rank based on index
            row = i // 7  # integer division for row
            col = i % 7  # modulus for column
            notation = f"{files[col]}{ranks[7 - row]}"  # Adjusting for A1 at bottom left

            if notation == f"{files[1]}{ranks[1]}":
                y_diff_pos1 = (int(corner[0][0]), int(corner[0][1]))
                # print(y_diff_pos1)
                y1 = int(y_diff_pos1[1])
            if notation == f"{files[2]}{ranks[1]}":
                y_diff_pos2 = (int(corner[0][0]), int(corner[0][1]))
                # print(y_diff_pos2)
                y2 = int(y_diff_pos2[1])

            y_diff = y2 - y1

            # print(y_diff)

        # Label each detected corner
        for i, corner in enumerate(corners):
            # Calculate file and rank based on index
            row = i // 7  # integer division for row
            col = i % 7  # modulus for column
            notation = f"{files[col]}{ranks[7 - row]}"  # Adjusting for A1 at bottom left

            # --------------------DOES THE A1 - G1-----------------------------------

            if notation == f"{files[col]}{ranks[1]}":
                new_n = f"{files[col]}{ranks[0]}"

                # print(f"{files[col]}{ranks[1]}")
                saved_pos = (int(corner[0][0]) - int(x_diff), int(corner[0][1]))
                cv2.putText(image, new_n, saved_pos, cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 1)

                center_pos = (int(corner[0][0]) - int(x_diff / 2), int(corner[0][1]) - int(y_diff / 2))
                position_dict[new_n] = (center_pos, "1")

                cv2.circle(image, center_pos, 3, (0, 255, 0), -1)  # Red color, filled circle

            # ----------------------------------------------DEAL WITH H2-H7------------------------------------------

            if notation == f"{files[6]}{ranks[7 - row]}":
                # print(f"{files[7]}{ranks[7-row]}")
                new_n = f"{files[7]}{ranks[7 - row]}"

                saved_pos = (
                int(corner[0][0]), int(corner[0][1]) + y_diff)  # NEED TO GET THE RIGHT Y_DIFF BUT THIS IS FINE FOR NOW
                cv2.putText(image, new_n, saved_pos, cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 1)

                center_pos = (int(corner[0][0]) + int(x_diff / 2), int(corner[0][1]) + int(y_diff / 2))
                position_dict[new_n] = (center_pos, "1")

                cv2.circle(image, center_pos, 3, (255, 0, 255), -1)  # purple color, filled circle

            # ----------------------H1 ----------------------------------------------------------

            if notation == f"{files[6]}{ranks[1]}":
                new_n = f"{files[7]}{ranks[0]}"

                # print(f"{files[col]}{ranks[1]}")
                saved_pos = (int(corner[0][0]) - int(x_diff), int(corner[0][1] + y_diff))
                cv2.putText(image, new_n, saved_pos, cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 1)

                center_pos = (int(corner[0][0]) - int(x_diff / 2), int(corner[0][1]) + int(y_diff / 2))
                position_dict[new_n] = (center_pos, "1")

                cv2.circle(image, center_pos, 3, (255, 0, 0), -1)  # Red color, filled circle

            # -----------------------------EVERYTHING ELSE----------------------------------------------------------------------
            # Draw the notation on the image
            corner_position = (int(corner[0][0]), int(corner[0][1]))

            # print(corner_position)
            cv2.putText(image, notation, corner_position, cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 1)
            # print(notation)

            center_pos = (int(corner[0][0]) + int(x_diff / 2), int(corner[0][1]) - int(y_diff / 2))
            position_dict[notation] = (center_pos, "1")

            cv2.circle(image, center_pos, 3, (0, 0, 255), -1)  # Red color, filled circle

    re_image = cv2.resize(image, (800, 800))
    img_name = os.path.join(folder_path, f"calibrate.png")
    cv2.imwrite(img_name, frame)
    print(f"Screenshot taken and saved as {img_name}.")
    cv2.imshow('Chessboard Outline', re_image)
    defult_dict = position_dict




def find_ar(frame):
    global count_1s, position_dict, board, white, fen_2,p_move, message  # Add 'board' to the global scope


    Turn_done = False
    C_c = False

    while C_c == False:
        ret, frame = cap.read()  # Read from webcam
        if not ret:
            print("Error: Could not read frame.")
            break

        try:
            gray_image2 = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            markerCorners, markerIds, _ = detector.detectMarkers(gray_image2)
            temp = copy.deepcopy(position_dict)

            if markerIds is not None:

                for i, markerId in enumerate(markerIds.flatten()):
                    corners = markerCorners[i][0]
                    marker_center = np.mean(corners, axis=0).astype(int)
                    mx, my = marker_center

                    closest_square = None
                    min_dist = float('inf')

                    for square, (center, label) in position_dict.items():
                        px, py = center
                        distance = np.sqrt((px - mx) ** 2 + (py - my) ** 2)

                        if distance < min_dist:
                            min_dist = distance
                            closest_square = square

                    if closest_square and min_dist < 25:
                        position_dict[closest_square] = ((mx, my), marker_labels.get(markerId, f"ID: {markerId}"))

                    x1, y1 = corners[0].astype(int)
                    x2, y2 = corners[2].astype(int)

                    label = marker_labels.get(markerId, f"ID: {markerId}")
                    cv2.putText(frame, label, (x1, y1), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2, cv2.LINE_AA)
                    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 255), 2)

            cv2.imshow("AR Markers", frame)

            # Initialize the board once if it doesn't exist
            if 'board' not in globals():
                board = [['1' for _ in range(8)] for _ in range(8)]

            # Update only the detected pieces where the board square is '1'
            for position, (coords, piece) in position_dict.items():
                file, rank = position[0], position[1]
                row = 8 - int(rank)
                col = ord(file) - ord('A')
                # Only update if the board square is '1'
                if board[row][col] == '1':
                    board[row][col] = piece[0]
            if white == True:
                num_1 = sum(row.count('1') for row in board)
                print("\nNumber of empty squares: ", num_1)

                if num_1 < count_1s:
                    board = [['1' for _ in range(8)] for _ in range(8)]

                elif num_1 == count_1s + 1 : #check player captures
                    p_m , cap_p = update_fen(board, white)
                    if cap_p:
                        count_1s += 1
                        p_move = str(p_m[1:])

                elif num_1 == count_1s : #should be count_1s

                    # print("Positions filled")
                    p_m, cap_p = update_fen(board, white)
                    white = False
                    p_move = str(p_m[1:])
                    update_log(p_move)
                    print("game moves: ", log_moves)
                    check_num, send_take = analyze_moves_with_stockfish(log_moves)
                    print("check_num from player move: ",check_num)
                    board = board = [['1' for _ in range(8)] for _ in range(8)]

                    # count += 1
                    count_1s = 32 + int(check_num)
                    print("cout1s was updated to at player: ", count_1s)
                    Turn_done = True
                    time.sleep(2)




            elif white == False:
                # user_moves = input("Enter moves separated by spaces (e.g., e4 e5 Nf3 Nc6): ").split()
                print("\n\n")
                white = True

                save_get = get_best_move(log_moves)
                best_move = save_get[0]
                update_black(best_move)
                stock_fen = get_stock_fen(log_moves)

                print("Stockfish best move: ",best_move)
                print("\nTHE STOCK LOG: ", log_moves)
                print("Stockfish fen: ",stock_fen)
                check_num,  send_take = analyze_moves_with_stockfish(log_moves)
                print("check_num from stockfish move: ", check_num)
                print("Is it checkmate?", board2.is_checkmate())
                print("Is it check?", board2.is_check())
                if board2.is_check():
                    engine.say("CHECKKKKKKK")
                    engine.runAndWait()
                print("Is it stalemate?", board2.is_stalemate())
                if send_take:
                    message = f"{str(best_move)}k\n"
                else:
                    message = f"{str(best_move)}\n"

                print(message)
                leo.write(message.encode())
                time.sleep(2)


                fen_2 = stock_fen
                board = [['1' for _ in range(8)] for _ in range(8)]

                count_1s = 32 + int(check_num)
                print("cout1s was updated to at stockfish: ", count_1s)
                # count += int(check_num)
                Turn_done = True


            save_board = board
            print(save_board)
            position_dict.update(temp)

            if Turn_done:
                C_c = True


        except Exception as e:
            print(f"Error processing frame: {e}")


def get_stock_fen(moves, depth=20):

    board2 = chess.Board()

    # Apply given moves
    try:
        print("get_best_moves log: ",log_moves)
        for move in log_moves:
            board2.push_san(move)
    except ValueError:
        print(f"Invalid move detected: {move}. Please check your input.")
        return None

    # Get best move using Stockfish
    with chess.engine.SimpleEngine.popen_uci(stockfish_path) as engine:
        fen = board2.fen()
        return fen # Return best move in UCI format


def get_best_move(moves, depth=20):

    board2 = chess.Board()

    # Apply given moves
    try:
        print("get_best_moves log: ",log_moves)
        for move in log_moves:
            board2.push_san(move)
    except ValueError:
        print(f"Invalid move detected: {move}. Please check your input.")
        return None

    # Get best move using Stockfish
    with chess.engine.SimpleEngine.popen_uci(stockfish_path) as engine:
        result = engine.play(board2, chess.engine.Limit(depth=depth))
        fen = board2.fen()
        return result.move.uci() , fen # Return best move in UCI format


def update_black(move):
    global board2
    log_moves.append(move)
    # print("Is it checkmate?", board2.is_checkmate())  # True
    # print("Is it check?", board2.is_check())  # True
    # print("Is it stalemate?", board2.is_stalemate())  # False




def update_log(move):
    global board2, count, white
    # log_moves.append(move)
    # for i in log_moves:
    #     board2.push_san(i)
    board2 = chess.Board()
    try:
        log_moves.append(move)
        for i in log_moves:
            board2.push_san(i)
        print(board2)
        print("Is it checkmate?", board2.is_checkmate())
        print("Is it check?", board2.is_check())  # True
        # print("Is it stalemate?", board.is_stalemate())
    except ValueError:
        print(f"Invalid move: {move}. Please try again.\n")
        white = True
        del log_moves[-1:]
        board2 = chess.Board()
        for i in log_moves:
            board2.push_san(i)
        print("what happend to move log:", log_moves)

def parse_fen(fen):
    """
    Parse the piece placement part of a FEN string into a 2D board representation.
    """
    board = []
    fen = fen.split(" ")[0]  # Extract only the board layout portion
    rows = fen.split("/")
    for row in rows:
        board_row = []
        for char in row:
            if char.isdigit():
                board_row.extend([""] * int(char))  # Empty squares
            else:
                board_row.append(char)
        board.append(board_row)
    return board


def find_move(fen1, fen2):
    """
    Compare two FEN strings and determine the move.
    """
    board1 = parse_fen(fen1)
    board2 = parse_fen(fen2)

    origin = None
    destination = None
    piece_moved = None
    piece_captured = None  # Track captured piece
    # castling_move =  None

    # for r in range(8):
    #     for c in range(8):
    #         piece1 = board1[r][c]
    #         piece2 = board2[r][c]
    #
    #         # Detect if a king is involved in castling
    #         if piece1 == "K" and piece2 == "":
    #             print("b1: ", board1[7][4])
    #             print("b2: ", board2[7][6])
    #             # White kingside castling (e1 -> g1)
    #             if r == 7 and c == 4 and board2[7][6] == "K":  # White castling kingside
    #                 castling_move = "e1g1"
    #             # White queenside castling (e1 -> c1)
    #             elif r == 7 and c == 4 and board2[7][2] == "K":  # White castling queenside
    #                 castling_move = "e1c1"

    for r in range(8):
        for c in range(8):
            piece1 = board1[r][c]
            piece2 = board2[r][c]

            if piece1 != piece2:
                if piece1 and not piece2:
                    # A piece was removed here -> origin of movement or capture
                    origin = (r, c)
                    piece_moved = piece1
                elif piece2 and (not piece1 or piece1.islower() != piece2.islower()):
                    # A new piece appears or replaces a captured piece
                    destination = (r, c)
                    if piece1 and piece1.islower() != piece2.islower():
                        piece_captured = piece1  # Captured piece

    return origin, destination, piece_moved, piece_captured



def coordinates_to_algebraic(r, c):
    """
    Convert board coordinates to algebraic notation (e.g., (6, 4) -> 'f2').
    """
    file = chr(c + ord('a'))  # Convert column index to file (a-h)
    rank = 8 - r  # Convert row index to rank (1-8)
    return f"{file}{rank}"


def read_arduino():
    global message
    start = True  # Start with calibration mode
    while True:
        ret, frame = cap.read()
        if not ret:
            print("Failed to grab frame")
            break

        cv2.imshow("CAM", frame)

        if start:
            if arduino.in_waiting > 0:
                data = arduino.readline().decode('utf-8').strip()
                print(f"Arduino says: {data}")

                if data == "Take the picture":
                    c_frame = frame
                    cv2.imshow("the pic", c_frame)
                    calib(c_frame)


            if cv2.waitKey(1) & 0xFF == ord('q'):  # Switch to find_ar mode
                cv2.destroyAllWindows()
                start = False  # Stop calibration mode

        else:  # Now in find_ar mode, waiting for a new button press
            if arduino.in_waiting > 0:
                data = arduino.readline().decode('utf-8').strip()
                # print(f"Arduino_WOWOW says: {data}")
                print("\n")

                if data == "Take the picture":
                    ar_frame = frame
                    cv2.imshow("New Frame for find_ar", ar_frame)
                    find_ar(ar_frame)  # Process new image in find_ar()
                    # print(f"OLD: {fen_1}")
                    # print(f"CURRENT: {fen_2}")
                if data == "Try Again":
                    print(f"Arduino says: {data}")
                    print(message)
                    leo.write(message.encode())

            if cv2.waitKey(1) & 0xFF == ord('q'):  # Allow exit
                cv2.destroyAllWindows()
                break

    cap.release()
    cv2.destroyAllWindows()


try:
    time.sleep(2)
    read_arduino()
except KeyboardInterrupt:
    print("Stopped by user")
finally:
    arduino.close()
    cap.release()
    cv2.destroyAllWindows()
    print("Resources released. Exiting.")
