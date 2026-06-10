import random
import string

def createRandomTXT(name, byteSize):
    chars = string.ascii_letters + string.digits
    
    with open(name, "w") as f:
        for _ in range(byteSize):
            f.write(random.choice(chars))

def createTestTXT():
    with open("server/archive-test.txt", "w") as f:
        f.write("Test\nALPHA\nLOrem is si merOL")

if __name__ == "__main__":
    createTestTXT()
    createRandomTXT("server/archive-1mb.txt", 1_009_000)
    createRandomTXT("server/archive-10mb.txt", 10_900_000)