import argparse

questions = [
    "If all roses are flowers and some flowers are red, can we deduce that some roses are red? Why?",
    "A brick weights 1 kg plus half of the weight of a brick. How much does the brick weight?",
    "If it rains, the ground will be wet. The ground is wet. Did it rain?",
    "You are facing north. If you turn 90° left on yourself three times in a row, which direction are you facing?",
    "On a street there is a man who offers you a bet: He throws a coin and if it is tails you get $3. If it is heads you lose $1. You can play the game how many times you want. Should you start playing? Why?",
	"You have a basket with 10 apples. You take away 3 apples. How many apples do you have?",
	"If a train leaves the station at 3:00 PM traveling at 60 km/h and another train leaves the same station at 4:00 PM traveling at 80 km/h, at what time will the second train catch up to the first?",
	"A farmer has 17 sheep, and all but 9 run away. How many sheep does the farmer have left?",
	"If you are in a dark room with a candle, a wood stove, and a gas lamp, and you only have one match, which do you light first?",
	"If a plane crashes on the border of two countries, where do they bury the survivors?"
]

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Retrieve a specific question by its index.")
    parser.add_argument(
        "-i", "--index", type=int, required=True,
        help=f"The index of the question to retrieve (between 0 and {len(questions) - 1})."
    )
    args = parser.parse_args()

    if 0 <= args.index < len(questions):
        print(questions[args.index])
    else:
        print(f"Error: Index out of range. Please provide an index between 0 and {len(questions) - 1}.")
