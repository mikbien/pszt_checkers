from enum import Enum
import copy

from helper import *


class Board:
    BOARD_SIZE = 8
    PIECES_COUNT = 12

    def __init__(self):
        self.board = [[None for i in range(self.BOARD_SIZE)]
                      for j in range(self.BOARD_SIZE)]
        #self.init_board()
        self.debug = False
        self.score = [self.PIECES_COUNT, self.PIECES_COUNT]

    def full_move(self, player, chosen_path):
        board = copy.deepcopy(self.board)
        print("Procesowana sciezka: " + str(chosen_path))
        processing = True
        move_from = Point(chosen_path.pop(0), chosen_path.pop(0))
        move_to = Point(chosen_path.pop(0), chosen_path.pop(0))

        should_capture = len(self.available_captures(player, move_from)) > 0

        while processing:
            x = self.score.copy()
            if not self.move(player, move_from, move_to):
                self.board = board
                return False
            if x == self.score and should_capture:
                self.board = board
                print("Player required to capture, wrong move")
                return False
            # player can move multiple times only when capturing
            if x == self.score and chosen_path:
                print("Too many move choices, wrong move")
                self.board = board
                return False
            should_capture = False
            if not chosen_path:
                break
            move_from = move_to
            move_to = (chosen_path.pop(0), chosen_path.pop(0))

        return True

    def move(self, player, start, to):
        # miki
        if not self._is_within_constraints(player, start, to):
            print("Error, wrong move")
            return
        from_piece = self.board[start.y][start.x]
        if from_piece.is_king:
            move_analysis = self._king_possible_capture(start, to)
            if not move_analysis[0]:
                return False
            else:
                # if a single piece was captured
                if move_analysis[1] is not None and move_analysis[2] == 1:
                    self.board[move_analysis[1][0]][move_analysis[1][1]] = None
                    if player.is_white:
                        self.score[0] -= 1
                    else:
                        self.score[1] -= 1
        elif not from_piece.is_king:
            if abs(to.y - start.y) == 2:
                self.board[average(to.y, start.y)][average(to.x, start.x)] = None
                if player.is_white:
                    self.score[0] -= 1
                else:
                    self.score[1] -= 1
        self.board[to.y][to.x], self.board[start.y][start.x] = self.board[start.y][start.x], \
                                                                             self.board[to.y][to.x]
        # if from_piece.is_white and to.y == 0 or (not from_piece.is_white) and to.y == self.BOARD_SIZE - 1:
        #     from_piece.is_king = True
        self._try_king(player, to)
        return True  # successful action

    def _execute_move(self, start, to):
        self.board[to.y][to.x] = self.board[start.y][start.x]
        self.board[start.y][start.x] = None
        piece = self.board[to.y][to.x]
        piece.y = to.y
        piece.x = to.x

    # check if this move is a capture
    def is_legal_capture(self, player, start, to):
        # miki
        captured_piece = None

        if self._is_within_constraints(player, start, to):
            from_piece = self.board[start.y][start.x]
            if from_piece.is_king:
                # handle king behavior
                return self._is_king_legal_capture(start, to)
            else:
                return self._is_man_legal_capture(start, to)
        return False, None

    # check if the move is legal when regarding game's rules
    def is_legal_move(self, player, start, to):
        # miki
        if self._is_within_constraints(player, start, to):
            from_piece = self.board[start.y][start.x]
            if from_piece.is_king:
                # handle king behavior
                return self._is_king_legal_move(start, to), None
            else:
                return self._is_man_legal_move(start, to), None
        return False, None

    def is_legal_action(self, player, start, to):
        # miki

        if self._is_within_constraints(player, start, to):
            from_piece = self.board[start.y][start.x]
            if from_piece.is_king:
                # handle king behavior
                return self._is_king_legal_action(start, to)
            else:
                return self._is_man_legal_action(start, to)
        return False

    # check basic game constraints
    def _is_within_constraints(self, player, start, to):

        if to.y not in range(self.BOARD_SIZE) or to.x not in range(self.BOARD_SIZE) or \
                start.y not in range(self.BOARD_SIZE) or start.x not in range(self.BOARD_SIZE):
            return False
        from_piece = self.board[start.y][start.x]
        # case: out of board bounds
        if from_piece is None:
            return False
        # case: piece not destined for given player
        if not from_piece.is_white == player.is_white:
            return False

        # case: piece cannot move like that because the x-travel distance must be equal to the y-travel distance
        if abs(to.y - start.y) != abs(to.x - start.x):
            return False
        # case: destination taken by another piece
        if self.board[to.y][to.x] is not None:
            return False
        return True

    # underscore na początku metody dajesz to taka kownencja zeby pokazac ze metoda ma byc private (bardziej
    # protected chyba w sumie)
    def _is_king_legal_action(self, start, to):
        result = self._king_possible_capture(start, to)
        if self._king_possible_capture(start, to)[0]:
            return True,
        return False

    def _is_king_legal_capture(self, start, to):
        result = self._king_possible_capture(start, to)
        if result[0] is True and result[1] is not None and result[2] == 1:
            return True, result[1]
        return False, None

    def _is_king_legal_move(self, start, to):
        result = self._king_possible_capture(start, to)
        if result[0] is True and result[1] is None and result[2] == 0:
            return True,
        return False

    # arg 0 tells the user, if the action is at all possible
    # arg 1 holds the captured piece - only, if it was captured
    # arg 2 hold the count of encountered pieces
    def _king_possible_capture(self, start, to):
        from_piece = self.board[start.y][start.x]

        dy = sgn(to.y - start.y)
        dx = sgn(to.x - start.x)

        is_action_possible = True
        captured_pieces = 0
        captured_piece = None  # only useful, if succesful capture

        # look for any pieces on the kings path
        # shift ranges by dx and dy so it goes from [start, stop) to (start, stop] (excludes start, includes stop)
        y_path = range(start.y + dy, to.y + dy, dy)
        x_path = range(start.x + dx, to.x + dx, dx)
        path = zip(y_path, x_path)
        for y, x in path:
            piece = self.board[y][x]
            if piece is not None:
                if piece.is_white == from_piece.is_white:
                    # collision with allied piece
                    is_action_possible = False
                    break
                else:
                    captured_pieces += 1
                    captured_piece = (y, x)
        if captured_pieces not in (0, 1):
            is_action_possible = False
        return is_action_possible, captured_piece, captured_pieces

    def _is_man_legal_action(self, start, to):

        if self._is_man_legal_capture(start, to) or self._is_man_legal_move(start, to):
            return True
        else:
            return False

    def _is_man_legal_capture(self, start, to):

        from_piece = self.board[start.y][start.x]
        delta_y = to.y - start.y

        if abs(delta_y) == 2:
            if self.board[average(to.y, start.y)][average(to.x, start.x)] is None:
                return False, None
            if self.board[average(to.y, start.y)][average(to.x, start.x)].is_white == \
                    from_piece.is_white:
                return False, None
            # if the move is too long in range ( not moving by one step and not capturing )
            else:
                return True, (average(to.y, start.y), average(to.x, start.x))
        return False, None

    # trying to move a piece without capturing
    def _is_man_legal_move(self, start, to):

        from_piece = self.board[start.y][start.x]
        delta_y = to.y - start.y

        if abs(delta_y) == 1:
            if from_piece.is_white and delta_y != -1 or not from_piece.is_white and delta_y != 1:
                return False
            else:
                return True
        return False

    # list all available moves
    def available_moves(self, player, start):
        move_list = []
        for row in range(self.BOARD_SIZE):
            for el in range(self.BOARD_SIZE):
                if self.is_legal_move(player, start, Point(row, el))[0]:
                    move_list.append(Point(row, el))
        #print(move_list)
        return move_list


    # TODO: pilnowac piece.y i piece.x i chyba score przy tyych wszystkich biciach
    def available_full_moves(self, player):
        full_moves = []
        for piece in player.get_pieces(self):
            start = Point(piece.y, piece.x)
            capture_tree = self.capture_trees(player, start)
            capture_tree.pop() # usuwa taka liste co ma sam pionek startowy, jakos to trzeba zmienic bo jest brzydko
            # since we build the tree starting from the latest moves, we need to reverse it
            capture_tree = [list(reversed(alist)) for alist in capture_tree]
            full_moves.extend(capture_tree)

            normal_moves = self.available_moves(player, Point(piece.y, piece.x))
            normal_tree = [[start, move] for move in normal_moves]
            full_moves.extend(normal_tree)

            # captures = self.available_captures(player, start)
            # if len(captures) > 0:
            #     board_copy = copy.deepcopy(self.board)
            #     for capture in captures:
            #         self.move(player, start, capture)
            #         full_moves.extend(self.capture_trees(player, capture))
            #         #full_moves.extend(self._capture_possibilities(player, capture, list(), [start]))
            #     self.board = board_copy
        return full_moves

    # def _capture_possibilities(self, player, start, all_moves, move_chain):
    #     captures = self.available_captures(player, start)
    #     move_chain.append(start)
    #     all_moves.append(copy.deepcopy(move_chain))
    #     if captures is None:
    #         return None
    #
    #     board_copy = copy.deepcopy(self.board)
    #
    #     for capture in captures:
    #         self.board = copy.deepcopy(self.board)
    #         self.move(player, start, capture)
    #         self._capture_possibilities(player, capture, all_moves, move_chain)
    #         #if new_chain is not None:
    #             #all_moves.append(new_chain)
    #
    #     self.board = board_copy
    #
    #     return all_moves

    def capture_trees(self, player, start):
        captures = self.available_captures(player, start)
        if start.y == 6 and start.x == 5:
            print('d00psko')
        if not captures:
            print(f'siema: {start}')
            return [[start]]
        board_copy = copy.deepcopy(self.board)
        tree = []
        for capture in captures:
            self.board = copy.deepcopy(board_copy)
            if not self.move(player, start, capture):
                print('nie move')
            child_tree = self.capture_trees(player, capture)
            for alist in child_tree:
                alist.append(start)
            tree.extend((child_tree))
        self.board = board_copy
        tree.append([start])
        return tree




    # list all available captures
    def available_captures(self, player, start):
        move_list = []
        for row in range(self.BOARD_SIZE):
            for el in range(self.BOARD_SIZE):
                if self.is_legal_capture(player, start, Point(row, el))[0]:
                    move_list.append(Point(row, el))
        #print(move_list)
        return move_list

    def init_board(self):
        def fill_row(row, start, is_white):
            for column in range(start, self.BOARD_SIZE, 2):
                self.board[row][column] = Piece(row, column, is_white, False)

        # fill black
        fill_row(0, 1, is_white=False)
        fill_row(1, 0, is_white=False)
        fill_row(2, 1, is_white=False)

        # fill white
        fill_row(self.BOARD_SIZE - 1, 0, is_white=True)
        fill_row(self.BOARD_SIZE - 2, 1, is_white=True)
        fill_row(self.BOARD_SIZE - 3, 0, is_white=True)

    def _get_king(self, player, point):
        self.board[point.y][point.x].is_king = True

    def _try_king(self, player, point):
        if (player.is_white and point.y == 0 or
                not player.is_white and point.y == self.BOARD_SIZE - 1):
            self._get_king(self, player, point)

    def get_pieces(self, player):
        pieces = []
        for row in self.board:
            for cell in row:
                tmp_piece = cell
                if tmp_piece is not None and tmp_piece.is_white == player.is_white:
                    pieces.append(tmp_piece)
        return pieces

    def display(self):

        def print_horizontal_lines():
            print("   ", end='')
            for _ in range(self.BOARD_SIZE):
                print("--- ", end='')

        # print column ids (letters)
        print("    ", end='')
        for i in range(self.BOARD_SIZE):
            col_id = chr(ord('A') + i) if self.debug is False else str(i)
            print(col_id + "   ", end='')
        print('')

        print_horizontal_lines()

        for y in range(self.BOARD_SIZE):
            print('')  # newline
            row_id = y + 1 if self.debug is False else y
            print(str(row_id) + ' ', end='')  # print row ids (numbers)
            for x in range(self.BOARD_SIZE):
                if self.board[y][x] is None:
                    print("|   ", end='')
                else:
                    print("|{:^3}".format(str(self.board[y][x])), end='')
            print("|")
            print_horizontal_lines()
        print('')  # newline


class Piece:

    def __init__(self, y, x, is_white, is_king=False):
        self.is_white = is_white
        self.is_king = is_king
        self.y = y
        self.x = x

    def __str__(self):
        if self.is_white:
            char = 'w'
        else:
            char = 'b'
        if self.is_king:
            char = char.upper()
        return char
    def __repr__(self):
        return self.__str__()


class Player:

    def __init__(self, is_white):
        self.is_white = is_white

    def get_move(self, board):
        moves = input(
            "Is white = " + str(self.is_white) + "\nEnter coordinates: <from_y> <from_x> <to_y> <to_x>").split()
        result = [int(x) for x in moves]  # albo result = list(map(int, moves))
        return result

    def get_pieces(self, board):
        return board.get_pieces(self)


class MinmaxAI(Player):

    def get_move(self):
        pass

    def minmax_score(self):
        pass


if __name__ == '__main__':
    brd = Board()
    brd.display()
