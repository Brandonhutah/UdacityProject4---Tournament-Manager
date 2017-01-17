#!/usr/bin/env python
#
# tournament.py -- implementation of a Swiss-system tournament
#
from contextlib import contextmanager
import psycopg2


def connect():
    """Connect to the PostgreSQL database.  Returns a database connection."""
    try:
        return psycopg2.connect("dbname=tournament")
    except:
        print("Connection failed")


@contextmanager
def get_cursor():
    """
    Query helper function using context lib. Creates a cursor from a database
    connection object, and performs queries using that cursor.
    """
    conn = connect()
    cursor = conn.cursor()
    try:
        yield cursor
    except:
        raise
    else:
        conn.commit()
    finally:
        cursor.close()
        conn.close()


def deleteMatches():
    """Remove all the match records from the database."""
    with get_cursor() as cursor:
        cursor.execute(
            "delete from matches")


def deletePlayers():
    """Remove all the player records from the database."""
    with get_cursor() as cursor:
        cursor.execute("delete from players")
    deleteMatches()


def countPlayers():
    """Returns the number of players currently registered."""
    with get_cursor() as cursor:
        cursor.execute("select count(*) from players")
        count = int(cursor.fetchone()[0])
    return count


def registerPlayer(name):
    """Adds a player to the tournament database.

    The database assigns a unique serial id number for the player.  (This
    should be handled by your SQL database schema, not in your Python code.)

    Args:
      name: the player's full name (need not be unique).
    """
    with get_cursor() as cursor:
        cursor.execute(
            "insert into players(name) values(%s)", (name,))


def playerStandings():
    """Returns a list of the players and their win records, sorted by wins.

    The first entry in the list should be the player in first place, or a player
    tied for first place if there is currently a tie.

    Returns:
      A list of tuples, each of which contains (id, name, wins, matches):
        id: the player's unique id (assigned by the database)
        name: the player's full name (as registered)
        wins: the number of matches the player has won
        matches: the number of matches the player has played
    """
    results = []
    with get_cursor() as cursor:
        cursor.execute(
            "select p.id, p.name, \
            (select count(*) from matches where winner = p.id) as wins, \
            (select count(*) from matches where (winner = p.id or loser = p.id)) as matches \
            from players p order by wins desc")
        standings = cursor.fetchall()

    for player in standings:
        results.append((player[0], player[1], player[2], player[3]))
    return results


def reportMatch(winner, loser):
    """Records the outcome of a single match between two players.

    Args:
      winner:  the id number of the player who won
      loser:  the id number of the player who lost
    """
    with get_cursor() as cursor:
        cursor.execute(
            "insert into matches(winner, loser) values(%s, %s)",
            (winner, loser,))


def swissPairings():
    """Returns a list of pairs of players for the next round of a match.

    Assuming that there are an even number of players registered, each player
    appears exactly once in the pairings.  Each player is paired with another
    player with an equal or nearly-equal win record, that is, a player adjacent
    to him or her in the standings.

    Returns:
      A list of tuples, each of which contains (id1, name1, id2, name2)
        id1: the first player's unique id
        name1: the first player's name
        id2: the second player's unique id
        name2: the second player's name
    """
    matchups = []
    standings = playerStandings()

    while len(standings) > 1:
        matchups.append(
            (standings[0][0], standings[0][1], standings[1][0], standings[1][1]))
        standings.pop(0)
        standings.pop(0)
    return matchups
