import argparse
import subprocess

def parse_arguments():
    parser = argparse.ArgumentParser(description='Keyrir timataka.py fyrir lista af URL-um.')
    parser.add_argument('--input_file', required=True,
                        help='Slóð að .txt skrá sem inniheldur URL-in.')
    parser.add_argument('--output_dir', default='data',
                        help='Mappa til að vista niðurstöðurnar.')
    parser.add_argument('--debug', action='store_true',
                        help='Vistar html í skrá til að skoða.')
    return parser.parse_args()

def main():
    args = parse_arguments()

    # Lesa inn URL-in úr .txt skránni
    with open(args.input_file, 'r') as f:
        urls = [line.strip().replace('&amp;', '&') for line in f if line.strip()]

    for url in urls:
        print(f"Keyri fyrir URL: {url}")
        cmd = ['python3', 'timataka.py', '--url', url, '--output_dir', args.output_dir]
        if args.debug:
            cmd.append('--debug')
        subprocess.run(cmd)

if __name__ == "__main__":
    main()
