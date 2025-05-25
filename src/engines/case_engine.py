from typing import Union, Optional

from engines.base_engine import BaseEngine
from facades import MarkMove, Board, CollapseMove, Engine, Cell, Mark
from exceptions import InvalidMoveException
from settings import PLAYER_1, PLAYER_2


class CaseEngine(BaseEngine):
    _ENGINE = Engine.CASE

    def _check_move_validity(self, move: Union[MarkMove, CollapseMove], previous_board: Board):
        # Common checks (currently none specific here as per instructions, winner check is in BaseEngine)

        if isinstance(move, MarkMove):
            # MarkMove specific checks
            if previous_board.cells_indexes_to_be_collapsed is not None:
                raise InvalidMoveException("Cannot make a MarkMove when a collapse is pending.")

            max_cell_index = previous_board.board_size * previous_board.board_size - 1
            if not (0 <= move.first_cell <= max_cell_index and 0 <= move.second_cell <= max_cell_index):
                raise InvalidMoveException("Cell index out of bounds.")

            if move.first_cell == move.second_cell:
                raise InvalidMoveException("MarkMove requires two different cells.")

            if previous_board.cells[move.first_cell].collapsed_mark is not None or \
               previous_board.cells[move.second_cell].collapsed_mark is not None:
                raise InvalidMoveException("Cannot place a mark in a collapsed cell.")

        elif isinstance(move, CollapseMove):
            # CollapseMove specific checks
            if previous_board.cells_indexes_to_be_collapsed is None:
                raise InvalidMoveException("No collapse is pending.")

            pending_cell1, pending_cell2 = previous_board.cells_indexes_to_be_collapsed
            if move.selected_cell not in [pending_cell1, pending_cell2]:
                raise InvalidMoveException("Selected cell for collapse is not one of the pending collapse cells.")
        
        else:
            # Should not happen with current type hints, but as a safeguard
            raise InvalidMoveException("Unknown move type.")

    def _update_board(self, move: Union[MarkMove, CollapseMove], board: Board):
        # Determine Current Player and Round
        max_round_index = 0
        for cell in board.cells:
            for mark in cell.quantic_marks:
                if mark.round_index > max_round_index:
                    max_round_index = mark.round_index
            if cell.collapsed_mark and cell.collapsed_mark.round_index > max_round_index:
                # Though collapsed marks might not be directly used for *next* round counting in all rulesets,
                # including it makes sure we are always moving forward.
                # The problem implies new marks are based on *all* existing marks.
                max_round_index = cell.collapsed_mark.round_index

        current_round_number = max_round_index + 1
        current_player_id = PLAYER_1 if current_round_number % 2 != 0 else PLAYER_2

        if isinstance(move, MarkMove):
            new_mark = Mark(player_id=current_player_id, round_index=current_round_number)
            
            # Add new_mark to the quantic_marks list of the specified cells
            board.cells[move.first_cell].quantic_marks.append(new_mark)
            board.cells[move.second_cell].quantic_marks.append(new_mark)
            
            # Reset cells_indexes_to_be_collapsed - this is done before cycle check
            board.cells_indexes_to_be_collapsed = None

            # Cycle Detection Logic
            newly_placed_mark = new_mark # Mark object created earlier in this method
            cell1_idx = move.first_cell
            cell2_idx = move.second_cell

            # Initial call to DFS
            # visited_marks_in_path is used to avoid re-using the same mark object in the current path construction.
            # current_path_marks tracks the sequence of marks forming the potential cycle.
            path = self._find_cycle_path(
                newly_placed_mark,
                cell1_idx,
                newly_placed_mark,
                cell2_idx,
                board,
                [],
                set()
            )

            if path:
                # Cycle detected
                board.cells_indexes_to_be_collapsed = (cell1_idx, cell2_idx)
                # Optional: store the path if needed later, e.g., board.cycle_path = path
                # For now, just setting cells_indexes_to_be_collapsed as per requirements.

        elif isinstance(move, CollapseMove):
            if board.cells_indexes_to_be_collapsed is None:
                # This should ideally be caught by _check_move_validity, but as a safeguard.
                raise InvalidMoveException("CollapseMove called but no collapse is pending.")

            cell1_idx, cell2_idx = board.cells_indexes_to_be_collapsed
            
            # 1. Identify the Initiating Mark
            # We need to find the specific mark instance that is present in both cell1_idx and cell2_idx
            # and is the one whose cycle completion triggered the collapse state.
            # This is typically the newest mark forming the cycle.
            initiating_mark = None
            highest_round_index = -1

            for mark_in_cell1 in board.cells[cell1_idx].quantic_marks:
                # Check if this mark also exists in cell2_idx
                if mark_in_cell1 in board.cells[cell2_idx].quantic_marks:
                    # This mark is in both cells. If there are multiple, pick the one with highest round_index.
                    if mark_in_cell1.round_index > highest_round_index:
                        highest_round_index = mark_in_cell1.round_index
                        initiating_mark = mark_in_cell1
            
            if initiating_mark is None:
                # This indicates an inconsistent state or error in logic leading up to this point.
                raise InvalidMoveException("Could not identify the initiating mark for collapse.")

            selected_cell_for_initiator = move.selected_cell
            other_cell_for_initiator = cell1_idx if selected_cell_for_initiator == cell2_idx else cell2_idx

            # 2. Retrieve the Cycle Path
            # The path will be like [M1_selected, M2, M3, ..., Mk, M1_other_side]
            # M1_selected is 'initiating_mark' at 'selected_cell_for_initiator'
            # M1_other_side is 'initiating_mark' at 'other_cell_for_initiator'
            cycle_path_full = self._find_cycle_path(
                initiating_mark,
                selected_cell_for_initiator,
                initiating_mark,
                other_cell_for_initiator,
                board,
                [],
                set()
            )

            if not cycle_path_full or len(cycle_path_full) < 2: # Path must exist and have at least the mark in two places
                # This should not happen if cells_indexes_to_be_collapsed was set due to a cycle.
                raise InvalidMoveException("Cycle path for collapse not found or invalid.")

            # 3. Perform the Collapse Cascade
            # Step 1 (Initiating Mark)
            board.cells[selected_cell_for_initiator].collapsed_mark = initiating_mark
            board.cells[selected_cell_for_initiator].quantic_marks.clear()
            
            # Remove initiating_mark from its other cell
            board.cells[other_cell_for_initiator].quantic_marks = [
                m for m in board.cells[other_cell_for_initiator].quantic_marks if m != initiating_mark
            ]

            # Step 2 (Propagate through the cycle)
            # The marks to be collapsed sequentially are cycle_path_full[1] through cycle_path_full[-2]
            # cycle_path_full[0] is initiating_mark in selected_cell (already handled)
            # cycle_path_full[-1] is initiating_mark in other_cell (already handled by removal)
            
            current_fixed_mark = initiating_mark
            # last_collapsed_cell_idx is the cell where current_fixed_mark just became classical.
            last_collapsed_cell_idx = selected_cell_for_initiator 

            # Iterate through the chain of marks that need to collapse due to the first one.
            # Example: path = [M1_sel, M2, M3, M1_oth]. Iterate M2, then M3.
            # M1_sel is current_fixed_mark. last_collapsed_cell_idx is where M1_sel is.
            # For M2 (next_mark_in_chain):
            #   shared_cell_idx_with_current_fixed_mark is last_collapsed_cell_idx (where M1 and M2 were together)
            #   cell_to_make_classical_for_next_mark is where M2's *other* instance is.
            
            # The actual marks in the chain to process are from index 1 up to (but not including) the last element.
            marks_in_chain_to_collapse = cycle_path_full[1:-1]

            for next_mark_in_chain in marks_in_chain_to_collapse:
                # shared_cell_idx_with_current_fixed_mark: where current_fixed_mark and next_mark_in_chain co-existed.
                # This cell *should* be last_collapsed_cell_idx because current_fixed_mark became classical there,
                # "freeing up" next_mark_in_chain.
                shared_cell_idx_with_current_fixed_mark = last_collapsed_cell_idx
                
                # Find where the other instance of next_mark_in_chain is. This is the cell that will now collapse.
                cell_to_make_classical_for_next_mark = self._get_other_cell_for_mark(
                    next_mark_in_chain, shared_cell_idx_with_current_fixed_mark, board
                )

                if cell_to_make_classical_for_next_mark is None:
                    # Should not happen in a valid cycle
                    raise InvalidMoveException(f"Could not find other cell for mark {next_mark_in_chain} during collapse cascade.")

                board.cells[cell_to_make_classical_for_next_mark].collapsed_mark = next_mark_in_chain
                board.cells[cell_to_make_classical_for_next_mark].quantic_marks.clear()

                # Remove next_mark_in_chain from the cell it shared with current_fixed_mark
                board.cells[shared_cell_idx_with_current_fixed_mark].quantic_marks = [
                    m for m in board.cells[shared_cell_idx_with_current_fixed_mark].quantic_marks if m != next_mark_in_chain
                ]
                
                current_fixed_mark = next_mark_in_chain
                last_collapsed_cell_idx = cell_to_make_classical_for_next_mark
            
            # 4. Finalize
            board.cells_indexes_to_be_collapsed = None

        # The board object is modified in place, so no explicit return is needed from this method.
        # The BaseEngine will return the board in the play_move response.

    def _get_other_cell_for_mark(self, mark_to_find: Mark, known_cell_idx: int, board: Board) -> Optional[int]:
        """Finds the other cell index where an instance of mark_to_find exists."""
        for i, cell in enumerate(board.cells):
            if i == known_cell_idx:
                continue
            # Check if mark_to_find is in this cell's quantic_marks
            # Mark dataclass instances with same attributes are considered equal.
            if mark_to_find in cell.quantic_marks:
                return i
        return None # Should ideally not happen if marks are placed correctly in pairs

    def _find_cycle_path(
        self,
        current_mark: Mark,
        current_cell_idx: int,
        target_mark: Mark, # This is the newly_placed_mark
        target_cell_idx: int, # This is the other cell of newly_placed_mark
        board: Board,
        current_path_marks: list[Mark], # Marks in the current path being explored
        visited_marks_in_current_dfs_path: set[Mark] # Marks already included in current_path_marks to avoid trivial loops
    ) -> Optional[list[Mark]]:
        """
        Performs a DFS to find a cycle of entangled marks.
        A cycle is found if we can trace a path from current_mark at current_cell_idx
        back to target_mark at target_cell_idx, using other entangled marks.
        """
        
        # Add current_mark to the path and visited set for this DFS exploration
        current_path_marks.append(current_mark)
        visited_marks_in_current_dfs_path.add(current_mark)

        # Explore marks in the current_cell_idx
        for other_mark_in_cell in board.cells[current_cell_idx].quantic_marks:
            if other_mark_in_cell == current_mark: # Don't try to transition with the same mark instance from the same cell
                continue

            if other_mark_in_cell in visited_marks_in_current_dfs_path: # Avoid re-using a mark already in the current path
                continue

            # Find the other cell where other_mark_in_cell is located
            next_cell_idx = self._get_other_cell_for_mark(other_mark_in_cell, current_cell_idx, board)

            if next_cell_idx is None: # Should not happen in a consistent board state
                continue

            # Check for cycle completion:
            # Is this other_mark_in_cell the target_mark (newly_placed_mark) we are looking for?
            # And is it located in the target_cell_idx (the other cell of newly_placed_mark)?
            if other_mark_in_cell == target_mark and next_cell_idx == target_cell_idx:
                # Cycle found
                return current_path_marks + [target_mark] # Path includes current_path_marks and the final target_mark

            # Recursive step: try to find a path from other_mark_in_cell at next_cell_idx
            # Create new list for current_path_marks for the recursive call to ensure path isolation
            # Create new set for visited_marks_in_current_dfs_path for the recursive call
            path_found = self._find_cycle_path(
                other_mark_in_cell,
                next_cell_idx,
                target_mark,
                target_cell_idx,
                board,
                list(current_path_marks), # Pass a copy for the new branch
                set(visited_marks_in_current_dfs_path) # Pass a copy
            )
            if path_found:
                return path_found # Propagate the found path upwards

        # Backtrack: No cycle found from current_mark via its neighbors in this cell
        # No need to explicitly remove from current_path_marks or visited_marks_in_current_dfs_path
        # as copies are passed in recursion. If this function returns None, the caller
        # knows this path didn't lead to a solution.
        return None

    def _get_winner(self, board: Board) -> Optional[str]:
        size = board.board_size

        # Helper to get player_id from a cell's collapsed_mark
        def get_player_id(cell_index: int) -> Optional[str]:
            mark = board.cells[cell_index].collapsed_mark
            return mark.player_id if mark else None

        # Check Rows
        for r in range(size):
            first_player_in_row = get_player_id(r * size)
            if first_player_in_row is None:
                continue  # Row cannot be a winning row if the first cell is not collapsed

            is_winning_row = True
            for c in range(1, size):
                if get_player_id(r * size + c) != first_player_in_row:
                    is_winning_row = False
                    break
            if is_winning_row:
                return first_player_in_row

        # Check Columns
        for c in range(size):
            first_player_in_col = get_player_id(c)
            if first_player_in_col is None:
                continue  # Column cannot be a winning column if the first cell is not collapsed

            is_winning_col = True
            for r in range(1, size):
                if get_player_id(r * size + c) != first_player_in_col:
                    is_winning_col = False
                    break
            if is_winning_col:
                return first_player_in_col

        # Check Main Diagonal (top-left to bottom-right)
        first_player_main_diag = get_player_id(0)
        if first_player_main_diag is not None:
            is_winning_main_diag = True
            for i in range(1, size):
                if get_player_id(i * size + i) != first_player_main_diag:
                    is_winning_main_diag = False
                    break
            if is_winning_main_diag:
                return first_player_main_diag

        # Check Anti-Diagonal (top-right to bottom-left)
        first_player_anti_diag = get_player_id(size - 1)
        if first_player_anti_diag is not None:
            is_winning_anti_diag = True
            # Start check from the second element on the anti-diagonal
            # For i=0, cell is (size-1) -> already checked (first_player_anti_diag)
            # For i=1, cell is 1*size + (size-1-1) = size + size - 2
            # For i=k, cell is k*size + (size-1-k)
            # The loop for checking should go from i=1 to size-1.
            # The first element of the anti-diagonal is (0, size-1) = index size-1
            # The second element is (1, size-2) = index 1*size + (size-2)
            # The i-th element (0-indexed on diagonal) is (i, size-1-i) = index i*size + (size-1-i)
            for i in range(1, size): # Iterate for the remaining size-1 elements
                cell_idx_on_anti_diag = i * size + (size - 1 - i)
                if get_player_id(cell_idx_on_anti_diag) != first_player_anti_diag:
                    is_winning_anti_diag = False
                    break
            if is_winning_anti_diag:
                return first_player_anti_diag
        
        # No Winner
        return None
