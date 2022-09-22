import json

def main():
    base_path = "analysis_result/initial-filter/"
    groups = ['barb','dsmp','kpop']
    pranith_groups = ['joer','nfts','star']
    for group in groups:
        path = base_path + group + "/word_frequency.json"
        with open(path) as f:
            wordlist = {'keep': {}, 'removed': {}}
            data = json.load(f)
            print(f'There are {len([c for c in data.values() if c > 100])} words in {group}')
            accepted = 0
            for word,count in list(data.items()):
                if count < 100:
                    break
                keep = input(f'[{group},{accepted}] {word}({count}) (y/n): ')
                if keep == '':
                    accepted += 1
                    wordlist['keep'][word] = count
                else:
                    wordlist['removed'][word] = count
            # write wordlist to file

            json.dump(wordlist, open(base_path + group + '/word_frequency_filtered.json', 'w'))

if __name__ == "__main__":
    main()