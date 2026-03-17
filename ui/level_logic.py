#more levels logic will be added for different levels with different mechanics and puzzles
class level2:
    """Tracks lever states and spike activation for level 2.

    All four levers must be pulled to deactivate the spikes and allow the
    player to progress.
    """

    def __init__(self) -> None:
        self.all_levers_pulled: bool = False

        self.spike_activated: bool = True
        self.num_levers_pulled: int = 0
        # dictionary used to trck level states
        self.lever_states: dict[str, bool] = {
            'lever1': False,
            'lever2': False,
            'lever3': False,
            'lever4': False
        }

    def pull_lever(self, lever_id: str) -> bool:
        """Mark a lever as pulled.

        Args:
            lever_id: Identifier of the lever (e.g. ``'lever1'``).

        Returns:
            ``True`` if the lever was newly pulled, ``False`` if it was already
            in the pulled state or the ID is invalid.
        """

        # check if the lever ID is valid and not already pulled then update state
        if lever_id in self.lever_states and not self.lever_states[lever_id]:
            self.lever_states[lever_id] = True
            self.num_levers_pulled += 1
            return True
        return False

    def update(self) -> None:
        """
        Check whether all levers have been pulled and update game state
        accordingly (deactivating spikes when the condition is met).

        """

        #4 levers in total so when all 4 are pulled, deactivate spikes
        if self.num_levers_pulled == 4:
            self.all_levers_pulled = True
            self.spike_activated = False
