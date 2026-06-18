"""
Run: python test_enhancer.py
Submits all test songs concurrently through the enhancer queue and reports
what album/genre data was added. 
Expect ~0.2s per song due to LastFM rate limiting, if metadata is incomplete expect additional ~1s per song due to MB rate limiting.
"""
import sys
import pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))

from concurrent.futures import ThreadPoolExecutor, as_completed
from downloader.enhancer import Enhancer
from downloader.dl_types import TrackMetadata

# (title, artist, duration_seconds)
TEST_SONGS = [
    ("Bohemian Rhapsody", "Queen", 354),
    ("Hotel California", "Eagles", 391),
    ("Stairway to Heaven", "Led Zeppelin", 482),
    ("Smells Like Teen Spirit", "Nirvana", 301),
    ("Like a Rolling Stone", "Bob Dylan", 369),
    ("Purple Haze", "Jimi Hendrix", 170),
    ("Johnny B. Goode", "Chuck Berry", 162),
    ("Good Vibrations", "The Beach Boys", 215),
    ("Superstition", "Stevie Wonder", 245),
    ("What's Going On", "Marvin Gaye", 235),
    ("Respect", "Aretha Franklin", 147),
    ("Lose Yourself", "Eminem", 326),
    ("HUMBLE.", "Kendrick Lamar", 177),
    ("God's Plan", "Drake", 198),
    ("Old Town Road", "Lil Nas X", 113),
    ("Shape of You", "Ed Sheeran", 234),
    ("Rolling in the Deep", "Adele", 228),
    ("Someone Like You", "Adele", 285),
    ("Blinding Lights", "The Weeknd", 200),
    ("Starboy", "The Weeknd", 230),
    ("Bad Guy", "Billie Eilish", 194),
    ("Happier", "Olivia Rodrigo", 149),
    ("drivers license", "Olivia Rodrigo", 242),
    ("Levitating", "Dua Lipa", 204),
    ("Don't Start Now", "Dua Lipa", 183),
    ("As It Was", "Harry Styles", 167),
    ("Heat Waves", "Glass Animals", 238),
    ("Stay", "The Kid LAROI", 141),
    ("Peaches", "Justin Bieber", 198),
    ("Industry Baby", "Lil Nas X", 212),
    ("Watermelon Sugar", "Harry Styles", 174),
    ("Golden Hour", "JVKE", 209),
    ("Ghost", "Justin Bieber", 153),
    ("traitor", "Olivia Rodrigo", 231),
    ("good 4 u", "Olivia Rodrigo", 178),
    ("Montero", "Lil Nas X", 137),
    ("Butter", "BTS", 164),
    ("Dynamite", "BTS", 202),
    ("Permission to Dance", "BTS", 185),
    ("Take On Me", "a-ha", 225),
    ("Sweet Child O' Mine", "Guns N' Roses", 356),
    ("November Rain", "Guns N' Roses", 537),
    ("Enter Sandman", "Metallica", 331),
    ("Master of Puppets", "Metallica", 515),
    ("Everlong", "Foo Fighters", 250),
    ("Learn to Fly", "Foo Fighters", 238),
    ("Under the Bridge", "Red Hot Chili Peppers", 277),
    ("Californication", "Red Hot Chili Peppers", 321),
    ("Black Hole Sun", "Soundgarden", 325),
    ("Jeremy", "Pearl Jam", 331),
    ("Creep", "Radiohead", 239),
    ("Karma Police", "Radiohead", 264),
    ("Fake Plastic Trees", "Radiohead", 285),
    ("Seven Nation Army", "The White Stripes", 231),
    ("Mr. Brightside", "The Killers", 222),
    ("Somebody Told Me", "The Killers", 197),
    ("Take Me Out", "Franz Ferdinand", 237),
    ("Chelsea Dagger", "The Fratellis", 253),
    ("Float On", "Modest Mouse", 213),
    ("Such Great Heights", "The Postal Service", 264),
    ("The Less I Know the Better", "Tame Impala", 218),
    ("Borderline", "Tame Impala", 269),
    ("Feels Like We Only Go Backwards", "Tame Impala", 193),
    ("Electric Feel", "MGMT", 230),
    ("Kids", "MGMT", 305),
    ("Time to Pretend", "MGMT", 265),
    ("Dog Days Are Over", "Florence + the Machine", 254),
    ("Shake It Out", "Florence + the Machine", 252),
    ("Skinny Love", "Bon Iver", 218),
    ("Holocene", "Bon Iver", 346),
    ("Re: Stacks", "Bon Iver", 302),
    ("Sweet Disposition", "The Temper Trap", 232),
    ("Little Lion Man", "Mumford & Sons", 275),
    ("The Cave", "Mumford & Sons", 279),
    ("Home", "Edward Sharpe and the Magnetic Zeros", 306),
    ("Stubborn Love", "The Lumineers", 243),
    ("Ho Hey", "The Lumineers", 163),
    ("Mykonos", "Fleet Foxes", 276),
    ("White Winter Hymnal", "Fleet Foxes", 143),
    ("Helplessness Blues", "Fleet Foxes", 317),
    ("Lua", "Bright Eyes", 250),
    ("First Day of My Life", "Bright Eyes", 213),
    ("Video Games", "Lana Del Rey", 290),
    ("Summertime Sadness", "Lana Del Rey", 265),
    ("Young and Beautiful", "Lana Del Rey", 252),
    ("Ribs", "Lorde", 232),
    ("Tennis Court", "Lorde", 185),
    ("Team", "Lorde", 193),
    ("Royals", "Lorde", 193),
    ("Green Light", "Lorde", 234),
    ("Supercut", "Lorde", 252),
    ("Hard Place", "H.E.R.", 214),
    ("Best Part", "Daniel Caesar", 218),
    ("Get You", "Daniel Caesar", 265),
    ("Location", "Khalid", 218),
    ("Young Dumb & Broke", "Khalid", 196),
    ("Talk", "Khalid", 193),
    ("Passionfruit", "Drake", 295),
    ("Nights", "Frank Ocean", 307),
    ("Thinkin Bout You", "Frank Ocean", 201),
]


def test_one(enhancer: Enhancer, title: str, artist: str, duration: int):
    track = TrackMetadata(
        video_id=f"{artist}-{title}".replace(" ", "_").lower(),
        title=title,
        artist=artist,
        album="",
        genres=[],
        mbid="",
        duration_seconds=duration,
    )
    enhanced = enhancer.get_enhanced_data(track)
    return track, enhanced
"""
def test_two(enhancer: Enhancer_FM, title: str, artist: str, duration: float):
    track = TrackMetadata(
        video_id=f"{artist}-{title}".replace(" ", "_").lower(),
        title=title,
        artist=artist,
        album="",
        genres=[],
        mbid="",
        duration_seconds=duration,
    )
    enhanced = enhancer.get_enhanced_data(track)
    return track, enhanced
"""


def main():
    enhancer = Enhancer()

    added_album = []
    added_genre = []
    added_mbid = []
    added_both = []
    unchanged = []

    print(f"Submitting {len(TEST_SONGS)} songs concurrently (~{len(TEST_SONGS)}s due to rate limit)...\n")

    with ThreadPoolExecutor(max_workers=20) as pool:
        futures = {
            pool.submit(test_one, enhancer, title, artist, dur): (title, artist)
            for title, artist, dur in TEST_SONGS
        }
        for i, future in enumerate(as_completed(futures), 1):
            original, enhanced = future.result()
            got_album = bool(enhanced.album)
            got_genre = bool(enhanced.genres)
            got_mbid = bool(enhanced.mbid)
            print(f"[{i:>3}/{len(TEST_SONGS)}] {original.artist} - {original.title}"
                  + (f"  album={enhanced.album!r}" if got_album else "")
                  + (f"  genres={enhanced.genres!r}" if got_genre else "")
                  + (f"  mbid={enhanced.mbid!r}"   if got_mbid else ""))

            if got_mbid:
                added_mbid.append((original, enhanced))

            if got_album and got_genre:
                added_both.append((original, enhanced))
            elif got_album:
                added_album.append((original, enhanced))
            elif got_genre:
                added_genre.append((original, enhanced))
            else:
                unchanged.append(original)

    print("\n" + "=" * 60)
    print(f"Got album + genre : {len(added_both)}")
    print(f"Got mbid : {len(added_mbid)}")
    print(f"Got album only    : {len(added_album)}")
    print(f"Got genre only    : {len(added_genre)}")
    print(f"Unchanged         : {len(unchanged)}")
    print("=" * 60)

    if unchanged:
        print("\nNo data added for:")
        for t in unchanged:
            print(f"  {t.artist} - {t.title}")


if __name__ == "__main__":
    main()
