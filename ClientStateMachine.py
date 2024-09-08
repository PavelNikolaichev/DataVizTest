class ClientStateMachine:
    def __init__(self):
        """
        Initialize the client state machine.
        """
        self.STATES = {
            "State Choosing": 0,
            "Make Selection": 1,
            "Describe Selection": 2,
            "Plot Selection": 3,
        }
        self.state = self.STATES["State Choosing"]

    def get_state(self) -> int:
        """
        Get the state of the client state machine.

        Returns:
            int: The state of the client state machine.
        """
        return self.state

    def set_state(self, state: str):
        """
        Set the state of the client state machine.

        Args:
            state (str): The state to set.

        Raises:
            ValueError: If the state is not valid.
        """
        if state in self.STATES:
            self.state = self.STATES[state]
        else:
            raise ValueError(f"Invalid state: {state}")
