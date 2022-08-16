class Equalizer:
    """Represents a 15 band equalizer for lavalink"""

    max_bands: int = 15
    max_value = 1.0
    min_value = -0.25

    def __init__(self):
        self._bands: list = []

    def __setitem__(self, index: int, value: float):
        if index < 0 or index >= self.max_bands:
            raise IndexError("Index out of range")
        if value < self.min_value or value > self.max_value:
            raise ValueError("Value out of range")
        self._bands[index] = value

    def __getitem__(self, index: int) -> int:
        if index < 0 or index >= self.max_bands:
            raise IndexError("Index out of range")
        return self._bands[index]

    def set_bands(self, bands: list) -> None:
        """
        Set the equalizer bands to the given list.

        Args:
            bands: The list of bands to set
        """
        if len(bands) != self.max_bands:
            raise ValueError("Invalid number of bands")
        self._bands = bands

    def reset(self) -> None:
        """Reset the equalizer to its default state"""
        self._bands = [0] * self.max_bands

    def to_payload(self) -> list[dict]:
        """Convert the equalizer to a payload for lavalink"""
        return [{"band": i, "gain": self[i]} for i in range(self.max_bands)]

    @classmethod
    def flat(cls) -> "Equalizer":
        """Create a flat equalizer"""
        eq = cls()
        eq.set_bands([0] * cls.max_bands)
        return eq

    @classmethod
    def boosted(cls) -> "Equalizer":
        """Create a boosted equalizer"""
        eq = cls()
        eq.set_bands([-0.075, 0.125, 0.125, 0.1, 0.1, 0.05, 0.075, 0.0, 0.0, 0.0, 0.0, 0.0, 0.125, 0.15, 0.05])
        return eq

    @classmethod
    def bass_boosted(cls) -> "Equalizer":
        """Create a bass boosted equalizer"""
        eq = cls()
        eq.set_bands(
            [0.125, 0.25, -0.25, -0.125, 0, -0.0125, -0.025, -0.0175, 0, 0, 0.0125, 0.025, 0.375, 0.125, 0.125]
        )
        return eq

    @classmethod
    def treble_boosted(cls) -> "Equalizer":
        """Create a treble boosted equalizer"""
        eq = cls()
        eq[10] = 0.6
        eq[11] = 0.6
        eq[12] = 0.6
        eq[13] = 0.65
        return eq

    @classmethod
    def piano(cls) -> "Equalizer":
        """Create a piano equalizer"""
        eq = cls()
        eq.set_bands([-0.25, -0.25, -0.25, -0.125, 0.0, 0.25, 0.25, 0.0, -0.25, -0.25, 0.0, 0.0, 0.5, 0.25, -0.025])
        return eq

    @classmethod
    def earrape(cls) -> "Equalizer":
        """Create an earrape equalizer"""
        eq = cls()
        eq.set_bands([0.25, 0.5, -0.5, -0.25, 0, -0.0125, -0.025, -0.0175, 0, 0, 0.0125, 0.025, 0.375, 0.125, 0.125])
        return eq

    @classmethod
    def electronic(cls) -> "Equalizer":
        """Create an electronic equalizer"""
        eq = cls()
        eq.set_bands([0.375, 0.35, 0.125, 0, 0, -0.125, -0.125, 0, 0.25, 0.125, 0.15, 0.2, 0.25, 0.35, 0.4])
        return eq

    @classmethod
    def classical(cls) -> "Equalizer":
        """Create a classical equalizer"""
        eq = cls()
        eq.set_bands([0.375, 0.35, 0.125, 0, 0, 0.125, 0.55, 0.05, 0.125, 0.25, 0.2, 0.25, 0.3, 0.25, 0.3])
        return eq

    @classmethod
    def rock(cls) -> "Equalizer":
        """Create a rock equalizer"""
        eq = cls()
        eq.set_bands([0.3, 0.25, 0.2, 0.1, 0.05, -0.05, -0.15, -0.2, -0.1, -0.05, 0.05, 0.1, 0.2, 0.25, 0.3])
        return eq

    @classmethod
    def metal(cls) -> "Equalizer":
        """Create a metal equalizer"""
        eq = cls()
        eq.set_bands([0.0, 0.1, 0.1, 0.15, 0.13, 0.1, 0.0, 0.125, 0.175, 0.175, 0.125, 0.125, 0.1, 0.075, 0.0])
        return eq

    @classmethod
    def full(cls) -> "Equalizer":
        """Create a full equalizer"""
        eq = cls()
        eq.set_bands(
            [0.625, 0.275, 0.2625, 0.25, 0.25, 0.2375, 0.225, 0.25, 0.25, 0.25, 0.2625, 0.275, 0.625, 0.375, 0.375]
        )
        return eq
