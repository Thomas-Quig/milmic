# open word_frequency.json
import json
with open('word_frequency.json', 'r') as f:
    word_frequency = json.load(f)
    word_frequency = sorted(word_frequency.items(), key=lambda x: x[1], reverse=True)

json.dump({word[0]:word[1] for word in word_frequency}, open('word_frequency_sorted.json', 'w'))