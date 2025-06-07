#!/usr/bin/env python3
import requests
import json
import pprint
import time
import os

# Load cache if it exists
CACHE_FILE = "card_cache.json"
if os.path.exists(CACHE_FILE):
    with open(CACHE_FILE, "r") as f:
        card_cache = json.load(f)
else:
    card_cache = {}

# Step 1: YDK Extractor
with open('deck.ydk') as f:
    deck = f.read().splitlines()

deck.pop(0)  # Remove first line (e.g., "#main")
decksize = deck.index("#extra") if "#extra" in deck else len(deck)
deck = deck[:decksize]  # Slice deck up to "#extra"
deck = [line for line in deck if line.isdigit()]  # Only valid numeric card IDs
deck = list(set(deck))  # Remove duplicates

deckmonsters = {}

# Step 2: API Calls with Caching and Rate Limiting
for card in deck:
    print(f"Processing card ID: {card}")
    try:
        if card in card_cache:
            card_info = card_cache[card]
            print(f"Loaded card ID {card} from cache: {card_info['name']}")
        else:
            response = requests.get(f"https://db.ygoprodeck.com/api/v7/cardinfo.php?id={card}")
            time.sleep(0.1)  # Rate limit: 10 requests per second
            info = response.json()

            if "data" not in info:
                print(f"Card ID {card} not found or error in response.")
                continue

            card_info = info["data"][0]
            card_cache[card] = card_info  # Save to cache
            print(f"Fetched and cached card ID {card}: {card_info['name']}")

        if "Monster" in card_info["type"]:
            deckmonsters[card_info["name"]] = {
                "ATK": card_info.get("atk", 0),
                "DEF": card_info.get("def", 0),
                "Attribute": card_info.get("attribute", "Unknown"),
                "Type": card_info.get("race", "Unknown"),
                "Level": card_info.get("level", 0)
            }

    except Exception as e:
        print(f"Error processing card ID {card}: {e}")
        continue

# Save cache to file
with open(CACHE_FILE, "w") as f:
    json.dump(card_cache, f, indent=2)

# Step 3: Monster Bridge Logic

def getScore(card, comparison):
    return sum(1 for key in card if card[key] == comparison[key])

monsterbridges = {}

for card in deckmonsters:
    monsterbridges[card] = []
    for key in deckmonsters:
        if card == key:
            continue
        score = getScore(deckmonsters[card], deckmonsters[key])
        if score == 1:
            print(f"Card {card} bridges with {key}")
            monsterbridges[card].append(key)

print("\nMonster Bridges:")
pprint.pprint(monsterbridges)

# Step 4: Output Chainable Small World Lines

with open("output.txt", "w") as f:
    for card in monsterbridges:
        for key in monsterbridges[card]:
            for target in monsterbridges.get(key, []):
                line = f"Banish {card} ---> Reveal {key} ---> Add {target}"
                print(line)
                f.write(line + "\n")
