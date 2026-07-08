# Problem Set 2, hangman.py
# Name:
# Collaborators:
# Time spent:

import random
import string

# -----------------------------------
# HELPER CODE
# -----------------------------------

WORDLIST_FILENAME = "words.txt"

def load_words():
    """
    returns: list, a list of valid words. Words are strings of lowercase letters.

    Depending on the size of the word list, this function may
    take a while to finish.
    """
    print("Loading word list from file...")
    # inFile: file
    inFile = open(WORDLIST_FILENAME, 'r')
    # line: string
    line = inFile.readline()
    # wordlist: list of strings
    wordlist = line.split()
    print(" ", len(wordlist), "words loaded.")
    return wordlist

def choose_word(wordlist):
    """
    wordlist (list): list of words (strings)

    returns: a word from wordlist at random
    """
    return random.choice(wordlist)

# -----------------------------------
# END OF HELPER CODE
# -----------------------------------


# Load the list of words to be accessed from anywhere in the program
wordlist = load_words()

def has_player_won(secret_word, letters_guessed):
    """
    secret_word: string, the lowercase word the user is guessing
    letters_guessed: list (of lowercase letters), the letters that have been
        guessed so far

    returns: boolean, True if all the letters of secret_word are in letters_guessed,
        False otherwise
    """
    #LIST OF LETTERS IN SECRET WORD, THEN REMOVE ALL LETTERS THAT HAVE BEEN GUESSED. IF THE LIST IS EMPTY, THE PLAYER HAS WON
    secret_letters = list(secret_word)

    for letter in letters_guessed:
        if letter in secret_letters:
            while letter in secret_letters:
              secret_letters.remove(letter)
    
    if secret_letters == []:
        return True
    else:
        return False


def get_word_progress(secret_word, letters_guessed):
    """
    secret_word: string, the lowercase word the user is guessing
    letters_guessed: list (of lowercase letters), the letters that have been
        guessed so far

    returns: string, comprised of letters and asterisks (*) that represents
        which letters in secret_word have not been guessed so far
    """
    #CREATE A STRING OF THE SECRET WORD WITH ASTERISKS REPLACING UNGUESSED LETTERS
    progress = ""
    for letter in secret_word:
        if letter in letters_guessed:
            progress += letter
        else:
            progress += "*"
    return progress


def get_available_letters(letters_guessed):
    """
    letters_guessed: list (of lowercase letters), the letters that have been
        guessed so far

    returns: string, comprised of letters that represents which
      letters have not yet been guessed. The letters should be returned in
      alphabetical order
    """
    #CREATE A LIST OF ALL LETTERS, THEN REMOVE THE GUESSED LETTERS FROM IT
    entire = list(string.ascii_lowercase)
    for letter in letters_guessed:
        if letter.lower() in entire:
            entire.remove(letter.lower())
    return "".join(entire)


def hangman(secret_word, with_help):
    """
    secret_word: string, the secret word to guess.
    with_help: boolean, this enables help functionality if true.

    Starts up an interactive game of Hangman.

    * At the start of the game, let the user know how many
      letters the secret_word contains and how many guesses they start with.

    * The user should start with 10 guesses.

    * Before each round, you should display to the user how many guesses
      they have left and the letters that the user has not yet guessed.

    * Ask the user to supply one guess per round. Remember to make
      sure that the user puts in a single letter (or help character '!'
      for with_help functionality)

    * If the user inputs an incorrect consonant, then the user loses ONE guess,
      while if the user inputs an incorrect vowel (a, e, i, o, u),
      then the user loses TWO guesses.

    * The user should receive feedback immediately after each guess
      about whether their guess appears in the computer's word.

    * After each guess, you should display to the user the
      partially guessed word so far.

    -----------------------------------
    with_help functionality
    -----------------------------------
    * If the guess is the symbol !, you should reveal to the user one of the
      letters missing from the word at the cost of 3 guesses. If the user does
      not have 3 guesses remaining, print a warning message. Otherwise, add
      this letter to their guessed word and continue playing normally.

    Follows the other limitations detailed in the problem write-up.
    """
    #INTRO + SETUP FOR GUESSING
    print("Welcome to Hangman!")
    print("I am thinking of a word that is", len(secret_word), "letters long.")
    guesses_remaining = 10
    letters_guessed = []

    #GAME LOOP
    while has_player_won(secret_word, letters_guessed) == False and guesses_remaining > 0:
        print("You have", guesses_remaining, "guesses left.")
        print("Available letters:", get_available_letters(letters_guessed))
        guess = input("Please guess a letter: ").lower()

        if guess == "!":
            if with_help:
                if guesses_remaining >= 3:
                    for letter in secret_word:
                        if letter not in letters_guessed:
                            letters_guessed.append(letter)
                            guesses_remaining -= 3
                            print("Letter revealed:", letter)
                            print(get_word_progress(secret_word, letters_guessed))
                            print("------------------------")
                            break
                else:
                    print("Not enough guesses remaining to use help!")
                    print("------------------------")
            else:
                print("Help functionality is not enabled.")
                print("------------------------")
        elif len(guess) != 1 or not guess.isalpha():
            print("Invalid input. Please enter a single letter.")
            print("------------------------")
        elif guess in letters_guessed:
            print("You've already guessed that letter.")
            print("------------------------")
        else:
            letters_guessed.append(guess)
            if guess in secret_word:
                print("Good guess:", get_word_progress(secret_word, letters_guessed))
                print("------------------------")
            else:
                print("Oops! That letter is not in my word:", get_word_progress(secret_word, letters_guessed))
                print("------------------------")
                if guess in "aeiou":
                    guesses_remaining -= 2
                else:
                    guesses_remaining -= 1

    #GAME END
    if has_player_won(secret_word, letters_guessed):
        print("Congratulations, you won! The word was", secret_word + ".")
    else:
        print("Sorry, you ran out of guesses. The word was", secret_word + ".")
    
    #SCORE CALCULATION
    unique_letters = 0
    for letter in letters_guessed:
        if letter in secret_word:
            unique_letters += 1
    score = guesses_remaining + (4 * unique_letters) + (3 * len(secret_word))
    print("Your score is:", score)


# When you've completed your hangman function, scroll down to the bottom
# of the file and uncomment the lines to test

if __name__ == "__main__":
    # To test your game, uncomment the following three lines.

    secret_word = choose_word(wordlist)
    with_help = True
    print(secret_word)
    hangman(secret_word, with_help)

    # After you complete with_help functionality, change with_help to True
    # and try entering "!" as a guess!

    ###############

    # SUBMISSION INSTRUCTIONS
    # -----------------------
    # It doesn't matter if the lines above are commented in or not
    # when you submit your pset. However, please run ps2_student_tester.py
    # one more time before submitting to make sure all the tests pass.

