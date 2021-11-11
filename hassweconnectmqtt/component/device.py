class Device:
    identifiers: list
    manufacturer: str
    model: str
    name: str

    def __init__(self, name=None, manufacturer=None, model=None, identifiers=None) -> None:
        self.identifiers = identifiers
        self.manufacturer = manufacturer
        self.model = model
        self.name = name

    def to_object(self) -> object:
        o = {}
        if self.identifiers is not None:
            o['identifiers'] = self.identifiers
        
        if self.manufacturer is not None:
            o['manufacturer'] = self.manufacturer

        if self.manufacturer is not None:
            o['model'] = self.model

        if self.manufacturer is not None:
            o['name'] = self.name

        return o
