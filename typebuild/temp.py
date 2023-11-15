
class Vehicle:
    messages = []
    codeword = "secret"
    def __init__(self, make, model, year, color):
        self.make = make
        self.model = model
        self.year = year
        self.color = color

    def print_details(self):
        print(f"Make: {self.make}")
        print(f"Model: {self.model}")
        print(f"Year: {self.year}")
        print(f"Color: {self.color}")
        print(f"Code word: {self.codeword}")

class Car(Vehicle):
    def __init__(self, make, model, year, color):
        super().__init__(make, model, year, color)

class Truck(Vehicle):
    def __init__(self, make, model, year, color, num_wheels):
        super().__init__(make, model, year, color)
        self.num_wheels = num_wheels

    def print_details(self):
        super().print_details()
        print(f"Number of wheels: {self.num_wheels}")

askhok_leyland = Truck("Ashok Leyland", "Dost", 2018, "White", 4)
askhok_leyland.print_details()

maruti_800 = Car("Maruti", "800", 2000, "Red")
maruti_800.print_details()