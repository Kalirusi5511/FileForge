import unittest
from app.models import Library, Pokemon

class TestMVP(unittest.TestCase):
    def test_box(self):
        lib = Library.empty()
        self.assertEqual(len(lib.boxes), 1)
        self.assertEqual(len(lib.boxes[0].slots), 30)

    def test_roundtrip(self):
        lib = Library.empty()
        p = Pokemon(species="Pikachu", generation=9)
        lib.pokemon[p.id] = p
        copy = Library.from_dict(lib.to_dict())
        self.assertEqual(copy.pokemon[p.id].species, "Pikachu")

if __name__ == "__main__":
    unittest.main()
