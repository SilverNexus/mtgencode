# transform passes used to encode / decode cards
import re
import random

# These could probably use a little love... They tend to hardcode in lots
# of things very specific to the mtgjson format.

import utils

cardsep = utils.cardsep
fieldsep = utils.fieldsep
bsidesep = utils.bsidesep
newline = utils.newline
dash_marker = utils.dash_marker
bullet_marker = utils.bullet_marker
this_marker = utils.this_marker
counter_marker = utils.counter_marker
reserved_marker = utils.reserved_marker
choice_open_delimiter = utils.choice_open_delimiter
choice_close_delimiter = utils.choice_close_delimiter
x_marker = utils.x_marker
tap_marker = utils.tap_marker
untap_marker = utils.untap_marker
counter_rename = utils.counter_rename
unary_marker = utils.unary_marker
unary_counter = utils.unary_counter


# Name Passes.


def name_pass_1_sanitize(s):
    s = s.replace('!', '')
    s = s.replace('?', '')
    s = s.replace('-', dash_marker)
    s = s.replace('100,000', 'one hundred thousand')
    s = s.replace('1,000', 'one thousand')
    s = s.replace('1996', 'nineteen ninety-six')
    return s


# Name unpasses.


# particularly helpful if you want to call text_unpass_8_unicode later
# and NOT have it stick unicode long dashes into names.
def name_unpass_1_dashes(s):
    return s.replace(dash_marker, '-')


# Text Passes.


def text_pass_1_strip_rt(s):
    return re.sub(r'\(.*\)', '', s)


def text_pass_2_cardname(s, name):
    # Here are some fun edge cases, thanks to jml34 on the forum for 
    # pointing them out.
    if name == 'sacrifice':
        s = s.replace(name, this_marker, 1)
        return s
    elif name == 'fear':
        return s

    s = s.replace(name, this_marker)
    
    # So, some legends don't use the full cardname in their text box...
    # this check finds about 400 of them.
    nameparts = name.split(',')
    if len(nameparts) > 1:
        mininame = nameparts[0]
        new_s = s.replace(mininame, this_marker)
        if not new_s == s:
            s = new_s
        
    # A few others don't have a convenient comma to detect their nicknames,
    # so we override them here.
    overrides = [
        # detectable by splitting on 'the', though that might cause other issues
        'crovax',
        'rashka',
        'phage',
        'shimatsu',
        'hazoret',
        'rakdos',
        # random and arbitrary: they have a last name, 1996 world champion, etc.
        'world champion',
        'axelrod',
        'hazezon',
        'rubinia',
        'rasputin',
        'hivis',
    ]
    
    for override in overrides:
        s = s.replace(override, this_marker)

    # stupid planeswalker abilities
    s = s.replace('to him.', 'to ' + this_marker + '.')
    s = s.replace('to him this', 'to ' + this_marker + ' this')
    s = s.replace('to himself', 'to itself')
    s = s.replace("he's", this_marker + ' is')

    # sometimes we actually don't want to do this replacement
    s = s.replace('named ' + this_marker, 'named ' + name)
    s = s.replace('name is still ' + this_marker, 'name is still ' + name)
    s = s.replace('named keeper of ' + this_marker, 'named keeper of ' + name)
    s = s.replace('named kobolds of ' + this_marker, 'named kobolds of ' + name)
    s = s.replace('named sword of kaldra, ' + this_marker, 'named sword of kaldra, ' + name)

    return s

# convert word numbers, such as for quantity of tokens or drawing cards, to numbers
# so they can, in turn, be converted to unary.
# NOTE: This is messy due to the many uses of a in English. Only some are referring to
# the number 1 as a specific quantity instead of a threshold.
def text_pass_3a_word_numbers(s):
    # Handle Zero
    # Take some instances of 'no' and quantify them as 0
    s = s.replace(' gains no life', ' gains 0 life')
    s = s.replace(' share no ', ' share 0 ')
    s = s.replace(' no cards', ' 0 cards')
    s = s.replace('if no spells', 'if 0 spells')
    s = s.replace(' control no ', ' control 0 ')
    s = s.replace('if no creatures', 'if 0 creatures')
    s = s.replace('there are no ', 'there are 0 ')
    # Triggers for having no counters of a certain type.
    s = s.replace(r' has no ((\w+)|([\+\-]\d+\/[\+\-]\d+)) counters', r'has 0 \1 counters')

    # Start by replacing one. Do this first to ensure we keep modal spells/abilities separate from other things
    s = s.replace(' one ', ' 1 ')
    s = s.replace(' one, ', ' 1, ')
    # undo "one or more"...
    s = s.replace(' 1 or more ', ' one or more ')
    # Then undo any other "choose one" effects. This breaks the choose encoding otherwise.
    s = s.replace('choose 1 ', 'choose one ')
    s = s.replace('opponent chooses 1 ~', 'opponent chooses one ~')
    # Then reapply "Choose one of them" clauses
    s = s.replace('choose one of ', 'choose 1 of ')
    # And lets hit "One or two"
    s = s.replace('one or two ', '1 or 2 ')
    # Handle Krark's Thumb
    s = s.replace(' ignore one', ' ignore 1')
    # Handle "that many plus one"
    s = s.replace(' plus one', ' plus 1')
    # And a replacement effect "instead of one"
    s = s.replace(' instead of one', ' instead of 1')
    # Also changes of maximum hand size.
    s = s.replace(' reduced by one', ' reduced by 1')
    s = s.replace(' increased by one', ' increased by 1')
    # Also handle the opponent choosing one of several cards you reveal.
    s = s.replace(' opponent chooses one.', ' opponent chooses 1.')

    # Then we do "a", since it also means 1
    s = s.replace(' a ', ' 1 ')
    # Undo "It's still a land." phrase, since we want this usage of a to stay.
    s = s.replace(' still 1 ', ' still a ')
    # Get "Equip only as a sorcery" phrase, too.
    s = s.replace(' as 1 ', ' as a ')
    # Things like "from a graveyard" should also be undone
    s = s.replace(' from 1 ', ' from a ')
    # And then "anytime you could cast a sorcery" needs undoing, too.
    s = s.replace(' cast 1 ', ' cast a ')
    s = s.replace(' casts 1 ', ' casts a ')
    # And then "controls a" texts also stat
    s = s.replace(' control 1 ', ' control a ')
    s = s.replace(' controls 1 ', ' controls a ')
    # "becomes a" is also not needed to change
    s = s.replace(' becomes 1 ', ' becomes a ')
    s = s.replace(' become 1 ', ' become a ')
    # "into a" also needs to use "a", not 1
    s = s.replace(' into 1 ', ' into a ')
    # Banding and a few other things.
    s = s.replace(' in 1 ', ' in a ')
    # "Whenever a" triggers should also stay as "a", not "1"
    s = s.replace('whenever 1 ', 'whenever a ')
    # "becomes the target of a ..." also should stay using "a"
    s = s.replace(' of 1 ', ' of a ')
    # also correct combat damage to a player/creature
    s = s.replace(' to 1 ', ' to a ')
    # Except when you are targeting up to one
    s = s.replace(' up to a ', ' up to 1 ')
    # Also avoid a player controls being a 1
    s = s.replace(' 1 player control', ' a player control')
    # other than a should also be handled
    s = s.replace('other than 1 ', 'other than a ')
    # fix "with a" clauses
    s = s.replace(' with 1 ', ' with a ')
    # Enter the battlefield with clauses should use 1, though
    s = s.replace(' battlefield with a ', ' battlefield with 1 ')
    # Or effects are usually triggers, so use "a" as a threshold quantifier
    s = s.replace(' or 1 ', ' or a ')
    # Except searching effects, which are usually a card or another card.
    s = s.replace(' card or a ', ' card or 1 ')
    # 'That's' clauses are usually copies, so numeric quantity is useless.
    s = s.replace(' that\'s 1 ', ' that\'s a ')
    # "A source" seems to be better described using "a"
    s = s.replace(' 1 source ', ' a source ')
    # "Is a" clauses really are more clear without encoding "a"
    s = s.replace(' is 1 ', ' is a ')
    # "it's a" clauses should be caught, too
    s = s.replace(" it's 1 ", " it's a ")
    # "that a land" clauses and a few other "that a" clauses should really use "a"
    s = s.replace(" that 1 ", " that a ")
    # Handle if conditions that really want one or more to be true.
    s = s.replace(" if 1 ", " if a ")
    # "Reveals a number of" clauses should not be quantified.
    s = s.replace('reveals 1 number of ', 'reveals a number of ')
    s = s.replace('reveal 1 number of ', 'reveal a number of ')

    # Handle an, for when the item following a makes a vowel sound
    # Do this in pieces, since it seems to be select cases that need it.
    # Extra turns
    s = s.replace('take an ', 'take 1 ');
    # addtional card draw
    s = s.replace(' draws an ',' draws 1 ')
    # Extra combat phases
    s = s.replace(' is an additional ', ' is 1 additional ')
    # Extra main phases after extra combat phases/
    s = s.replace(' followed by an ', ' followed by 1 ')
    # Extra blocks per combat
    s = s.replace(' block an ', ' block 1 ')
    # Undo hundred-handed one and convert the actual number extra while we're here.
    s = s.replace(' block 1 additional ninety-nine ', ' block an additional 99 ')
    # Handle choosing a single item, usually an opponent. But its one, so encode it
    s = s.replace(' choose an ', ' choose 1 ')
    s = s.replace(' chooses an ', ' chooses 1 ')
    # Handle an enchantment or artifact in a list of items chosen
    # This requires a regular expression to actually do, since we sometimes have
    # a list of conditions where the "an" stands for "at least one", and sometimes
    # we are choosing exactly one of the type.
    s = re.sub(r' chooses (.*), an ', r' chooses \1, 1 ', s)
    # Handle sacrifice effects
    s = s.replace('sacrifice an ', 'sacrifice 1 ')
    # Handle putting things onto permanents and/or battlefields
    s = s.replace(' put an ', ' put 1 ')
    # Handle X/X and 8/8 tokens, since they use "an"
    s = s.replace(' create an ', ' create 1 ')
    # Handle things that enter the "battlefield with an" counter
    s = s.replace(' battlefield with an ', ' battlefield with 1 ')
    # Searching library for a single card
    s = s.replace(' library for an ', ' library for 1 ')
    # Play an additional can be play 1 additional
    s = s.replace('play an additional', 'play 1 additional')

    # Then we move on to other numbers
    s = s.replace(' two ', ' 2 ')
    s = s.replace(' two, ', ' 2, ')
    # Undo "If two or more XXXX are tied..." scenarios"
    s = s.replace('. if 2 or more ', '. if two or more ')
    # Replace choose two as well, to ensure the special choose encoding works.
    s = s.replace('choose 2 ', 'choose two ')
    # Except Seal of the Guildpact has us choose two colors. This can be quantified.
    s = s.replace('choose two colors', 'choose 2 colors')
    # And also choose two target should be quantified.
    s = s.replace('choose two target', 'choose 2 target')
    # And choose two of those
    s = s.replace('choose two of ', 'choose 2 of ') 

    # About two times three is at the end of a statement. We need to handle those.
    s = s.replace(' three ', ' 3 ')
    s = s.replace(' three.', ' 3.')

    # and some hand size and other modifiers also occur at statement ends for four.
    s = s.replace(' four ', ' 4 ')
    s = s.replace(' four.', ' 4.')

    # Monocolor god devotions for Theros gods has a comma after five.
    s = s.replace(' five ', ' 5 ')
    s = s.replace(' five,', ' 5,')

    s = s.replace(' six ', ' 6 ')

    # Jin-Gitaxias and multicolored Theros gods have punctuation after the number
    s = s.replace(' seven ', ' 7 ')
    s = s.replace(' seven,', ' 7,')
    s = s.replace(' seven.', ' 7.')

    s = s.replace(' eight ', ' 8 ')
    s = s.replace(' nine ', ' 9 ')
    s = s.replace(' ten ', ' 10 ')
    s = s.replace(' twelve ', ' 12 ')
    s = s.replace(' thirteen ', ' 13 ')
    s = s.replace(' fifteen ', ' 15 ')
    s = s.replace(' twenty ', ' 20 ')
    s = s.replace(' twenty-six ', ' 26 ')
    # Hundred-handed one is now handled above
    # s = s.replace(' ninety-nine ', ' 99 ')
    return s

def text_pass_3b_unary(s):
    return utils.to_unary(s)


# Run only after doing unary conversion.
def text_pass_4a_dashes(s):
    s = s.replace('-' + unary_marker, reserved_marker)
    s = s.replace('-', dash_marker)
    s = s.replace(reserved_marker, '-' + unary_marker)
    
    # level up is annoying
    levels = re.findall(r'level &\^*\-&', s)
    for level in levels:
        newlevel = level.replace('-', dash_marker)
        s = s.replace(level, newlevel)

    levels = re.findall(r'level &\^*\+', s)
    for level in levels:
        newlevel = level.replace('+', dash_marker)
        s = s.replace(level, newlevel)

    # and we still have the ~x issue
    return s


# Run this after fixing dashes, because this unbreaks the ~x issue.
# Also probably don't run this on names, there are a few names with x~ in them.
def text_pass_4b_x(s):
    s = s.replace(dash_marker + 'x', '-' + x_marker)
    s = s.replace('+x', '+' + x_marker)
    s = s.replace(' x ', ' ' + x_marker + ' ')
    s = s.replace('x:', x_marker + ':')
    s = s.replace('x~', x_marker + '~')
    s = s.replace(u'x\u2014', x_marker + u'\u2014')
    s = s.replace('x.', x_marker + '.')
    s = s.replace('x,', x_marker + ',')
    s = s.replace('x is', x_marker + ' is')
    s = s.replace('x can\'t', x_marker + ' can\'t')
    s = s.replace('x/x', x_marker + '/' + x_marker)
    s = s.replace('x target', x_marker + ' target')
    s = s.replace('si' + x_marker + ' target', 'six target')
    s = s.replace('avara' + x_marker, 'avarax')
    # there's also some stupid ice age card that wants -x/-y
    s = s.replace('/~', '/-')
    return s


# Call this before replacing newlines.
# This one ends up being really bad because of the confusion
# with 'counter target spell or ability'.
def text_pass_5_counters(s):
    # so, big fat old dictionary time!!!!!!!!!
    allcounters = [
        'time counter',
        'devotion counter',
        'charge counter',
        'ki counter',
        'matrix counter',
        'spore counter',
        'poison counter',
        'quest counter',
        'hatchling counter',
        'storage counter',
        'growth counter',
        'paralyzation counter',
        'energy counter',
        'study counter',
        'glyph counter',
        'depletion counter',
        'sleight counter',
        'loyalty counter',
        'hoofprint counter',
        'wage counter',
        'echo counter',
        'lore counter',
        'page counter',
        'divinity counter',
        'mannequin counter',
        'ice counter',
        'fade counter',
        'pain counter',
        #'age counter',
        'gold counter',
        'muster counter',
        'infection counter',
        'plague counter',
        'fate counter',
        'slime counter',
        'shell counter',
        'credit counter',
        'despair counter',
        'globe counter',
        'currency counter',
        'blood counter',
        'soot counter',
        'carrion counter',
        'fuse counter',
        'filibuster counter',
        'wind counter',
        'hourglass counter',
        'trap counter',
        'corpse counter',
        'awakening counter',
        'verse counter',
        'scream counter',
        'doom counter',
        'luck counter',
        'intervention counter',
        'eyeball counter',
        'flood counter',
        'eon counter',
        'death counter',
        'delay counter',
        'blaze counter',
        'magnet counter',
        'feather counter',
        'shield counter',
        'wish counter',
        'petal counter',
        'music counter',
        'pressure counter',
        'manifestation counter',
        #'net counter',
        'velocity counter',
        'vitality counter',
        'treasure counter',
        'pin counter',
        'bounty counter',
        'rust counter',
        'mire counter',
        'tower counter',
        #'ore counter',
        'cube counter',
        'strife counter',
        'elixir counter',
        'hunger counter',
        'level counter',
        'winch counter',
        'fungus counter',
        'training counter',
        'theft counter',
        'arrowhead counter',
        'sleep counter',
        'healing counter',
        'mining counter',
        'dream counter',
        'aim counter',
        'arrow counter',
        'javelin counter',
        'gem counter',
        'bribery counter',
        'mine counter',
        'omen counter',
        'phylactery counter',
        'tide counter',
        'polyp counter',
        'petrification counter',
        'shred counter',
        'pupa counter',
        'crystal counter',
        'egg counter',
        'plot counter',
        'hit counter',
        'brick counter',
        'unity counter',
        'prey counter',
        'slumber counter',
        'vortex counter',
        'landmark counter',
        'hour counter',
        'isolation counter',
        'fury counter',
        'silver counter',
        'experience counter',
        'spite counter'
    ]
    usedcounters = []
    for countername in allcounters:
        if countername in s:
            usedcounters += [countername]
            s = s.replace(countername, counter_marker + ' counter')
    
    # oh god some of the counter names are suffixes of others...
    shortcounters = [
        'age counter',
        'net counter',
        'ore counter',
    ]
    for countername in shortcounters:
        # SUPER HACKY fix for doubling season
        if countername in s and 'more counter' not in s:
            usedcounters += [countername]
            s = s.replace(countername, counter_marker + ' counter')
    
    # miraculously this doesn't seem to happen
    # if len(usedcounters) > 1:
    #     print usedcounters

    # we haven't done newline replacement yet, so use actual newlines
    if len(usedcounters) == 1:
        # and yeah, this line of code can blow up in all kinds of different ways
        s = 'countertype ' + counter_marker + ' ' + usedcounters[0].split()[0] + '\n' + s

    return s


# The word 'counter' is confusing when used to refer to what we do to spells
# and sometimes abilities to make them not happen. Let's rename that.
# Call this after doing the counter replacement to simplify the regexes.
counter_rename = 'uncast'
def text_pass_6_uncast(s):
    # pre-checks to make sure we aren't doing anything dumb
    # if '% counter target ' in s or '^ counter target ' in s or '& counter target ' in s:
    #     print s + '\n'
    # if '% counter a ' in s or '^ counter a ' in s or '& counter a ' in s:
    #     print s + '\n'
    # if '% counter all ' in s or '^ counter all ' in s or '& counter all ' in s:
    #     print s + '\n'
    # if '% counter a ' in s or '^ counter a ' in s or '& counter a ' in s:
    #     print s + '\n'
    # if '% counter that ' in s or '^ counter that ' in s or '& counter that ' in s:
    #     print s + '\n'
    # if '% counter @' in s or '^ counter @' in s or '& counter @' in s:
    #     print s + '\n'
    # if '% counter the ' in s or '^ counter the ' in s or '& counter the ' in s:
    #     print s + '\n'

    # counter target
    s = s.replace('counter target ', counter_rename + ' target ')
    # counter a
    s = s.replace('counter a ', counter_rename + ' a ')
    # counter all
    s = s.replace('counter all ', counter_rename + ' all ')
    # counters a
    s = s.replace('counters a ', counter_rename + 's a ')
    # countered (this could get weird in terms of englishing the word; lets just go for hilarious)
    s = s.replace('countered', counter_rename + 'ed')
    # counter that
    s = s.replace('counter that ', counter_rename + ' that ')
    # counter @
    s = s.replace('counter @', counter_rename + ' @')
    # counter it (this is tricky
    s = s.replace(', counter it', ', ' + counter_rename + ' it')
    # counter the (it happens at least once, thanks wizards!)
    s = s.replace('counter the ', counter_rename + ' the ')
    # counter up to
    s = s.replace('counter up to ', counter_rename + ' up to ')

    # check if the word exists in any other context
    # if 'counter' in (s.replace('% counter', '').replace('countertype', '')
    #                  .replace('^ counter', '').replace('& counter', ''):
    #     print s + '\n'

    # whew! by manual inspection of a few dozen texts, it looks like this about covers it.
    return s    
    

# Run after fixing dashes, it makes the regexes better, but before replacing newlines.
def text_pass_7_choice(s):
    # the idea is to take 'choose n ~\n=ability\n=ability\n'
    # to '[n = ability = ability]\n'
    
    def choice_formatting_helper(s_helper, prefix, count, suffix = ''):
        single_choices = re.findall(ur'(' + prefix + ur'\n?(\u2022.*(\n|$))+)', s_helper)
        for choice in single_choices:
            newchoice = choice[0]
            newchoice = newchoice.replace(prefix, unary_marker + (unary_counter * count) + suffix)
            newchoice = newchoice.replace('\n', ' ')
            if newchoice[-1:] == ' ':
                newchoice = choice_open_delimiter + newchoice[:-1] + choice_close_delimiter + '\n'
            else:
                newchoice = choice_open_delimiter + newchoice + choice_close_delimiter
            s_helper = s_helper.replace(choice[0], newchoice)
        return s_helper

    s = choice_formatting_helper(s, ur'choose one \u2014', 1)
    s = choice_formatting_helper(s, ur'choose one \u2014 ', 1) # ty Promise of Power
    s = choice_formatting_helper(s, ur'choose two \u2014', 2)
    s = choice_formatting_helper(s, ur'choose two \u2014 ', 2) # ty Profane Command
    s = choice_formatting_helper(s, ur'choose one or both \u2014', 0)
    s = choice_formatting_helper(s, ur'choose one or more \u2014', 0)
    s = choice_formatting_helper(s, ur'choose khans or dragons.', 1)
    # this is for 'an opponent chooses one', which will be a bit weird but still work out
    s = choice_formatting_helper(s, ur'chooses one \u2014', 1)
    # Demonic Pact has 'choose one that hasn't been chosen'...
    s = choice_formatting_helper(s, ur"choose one that hasn't been chosen \u2014", 1,
                                 suffix=" that hasn't been chosen")
    # 'choose n. you may choose the same mode more than once.'
    s = choice_formatting_helper(s, ur'choose three. you may choose the same mode more than once.', 3,
                                 suffix='. you may choose the same mode more than once.')

    return s


# do before removing newlines
# might as well do this after countertype because we probably care more about
# the location of the equip cost
def text_pass_8_equip(s):
    equips = re.findall(r'equip ' + utils.mana_json_regex + r'.?$', s)
    # there don't seem to be any cases with more than one
    if len(equips) == 1:
        equip = equips[0]
        s = s.replace('\n' + equip, '')
        s = s.replace(equip, '')

        if equip[-1:] == ' ':
            equip = equip[0:-1]

        if s == '':
            s = equip
        else:
            s = equip + '\n' + s

    nonmana = re.findall(ur'(equip\u2014.*(\n|$))', s)
    if len(nonmana) == 1:
        equip = nonmana[0][0]
        s = s.replace('\n' + equip, '')
        s = s.replace(equip, '')
        
        if equip[-1:] == ' ':
            equip = equip[0:-1]

        if s == '':
            s = equip
        else:
            s = equip + '\n' + s
        
    return s


def text_pass_9_newlines(s):
    return s.replace('\n', utils.newline)


def text_pass_10_symbols(s):
    return utils.to_symbols(s)


# reorder the lines of text into a canonical form:
# first enchant and equip
# then other keywords, one per line (things with no period on the end)
# then other abilities
# then kicker and countertype last of all
def text_pass_11_linetrans(s):
    # let's just not deal with level up
    if 'level up' in s:
        return s

    prelines = []
    keylines = []
    mainlines = []
    postlines = []

    lines = s.split(utils.newline)
    for line in lines:
        line = line.strip()
        if line == '':
            continue
        if not '.' in line:
            # because this is inconsistent
            line = line.replace(',', ';')
            line = line.replace('; where', ', where') # Thromok the Insatiable
            line = line.replace('; and', ', and') # wonky protection
            line = line.replace('; from', ', from') # wonky protection
            line = line.replace('upkeep;', 'upkeep,') # wonky protection
            line = line.replace('; land; or planeswalker', ', land, or planeswalker') # Imprisoned in the Moon
            sublines = line.split(';')
            for subline in sublines:
                subline = subline.strip()
                if 'equip' in subline or 'enchant' in subline:
                    prelines += [subline]
                elif 'countertype' in subline or 'kicker' in subline:
                    postlines += [subline]
                else:
                    keylines += [subline]
        elif u'\u2014' in line and not u' \u2014 ' in line:
            if 'equip' in line or 'enchant' in line:
                prelines += [line]
            elif 'countertype' in line or 'kicker' in line:
                postlines += [line]
            else:
                keylines += [line]
        else:
            mainlines += [line]

    alllines = prelines + keylines + mainlines + postlines
    return utils.newline.join(alllines)


# randomize the order of the lines
# not a text pass, intended to be invoked dynamically when encoding a card
# call this on fully encoded text, with mana symbols expanded
def separate_lines(text):
    # forget about level up, ignore empty text too while we're at it
    if text == '' or 'level up' in text:
        return [],[],[],[],[]
    
    preline_search = ['equip', 'fortify', 'enchant ', 'bestow']
    # probably could use optimization with a regex
    costline_search = [
        'multikicker', 'kicker', 'suspend', 'echo', 'awaken',
        'buyback', 'dash', 'entwine', 'evoke', 'flashback',
        'madness', 'megamorph', 'morph', 'miracle', 'ninjutsu', 'overload',
        'prowl', 'recover', 'reinforce', 'replicate', 'scavenge', 'splice',
        'surge', 'unearth', 'transmute', 'transfigure',
    ]
    # cycling is a special case to handle the variants
    postline_search = ['countertype']
    keyline_search = ['cumulative']

    prelines = []
    keylines = []
    mainlines = []
    costlines = []
    postlines = []

    lines = text.split(utils.newline)
    # we've already done linetrans once, so some of the irregularities have been simplified
    for line in lines:
        if not '.' in line:
            if any(line.startswith(s) for s in preline_search):
                prelines.append(line)
            elif any(line.startswith(s) for s in postline_search):
                postlines.append(line)
            elif any(line.startswith(s) for s in costline_search) or 'cycling' in line:
                costlines.append(line)
            else:
                keylines.append(line)
        elif (utils.dash_marker in line and not 
              (' '+utils.dash_marker+' ' in line or 'non'+utils.dash_marker in line)):
            if any(line.startswith(s) for s in preline_search):
                prelines.append(line)
            elif any(line.startswith(s) for s in costline_search) or 'cycling' in line:
                costlines.append(line)
            elif any(line.startswith(s) for s in keyline_search):
                keylines.append(line)
            else:
                mainlines.append(line)
        elif ': monstrosity' in line:
            costlines.append(line)
        else:
            mainlines.append(line)

    return prelines, keylines, mainlines, costlines, postlines

choice_re = re.compile(re.escape(utils.choice_open_delimiter) + r'.*' + 
                       re.escape(utils.choice_close_delimiter))
choice_divider = ' ' + utils.bullet_marker + ' '
def randomize_choice(line):
    choices = re.findall(choice_re, line)
    if len(choices) < 1:
        return line
    new_line = line
    for choice in choices:
        parts = choice[1:-1].split(choice_divider)
        if len(parts) < 3:
            continue
        choiceparts = parts[1:]
        random.shuffle(choiceparts)
        new_line = new_line.replace(choice, 
                                    utils.choice_open_delimiter +
                                    choice_divider.join(parts[:1] + choiceparts) +
                                    utils.choice_close_delimiter,
                                    1)
    return new_line
    
def randomize_lines(text):
    if text == '' or 'level up' in text:
        return text

    prelines, keylines, mainlines, costlines, postlines = separate_lines(text)

    new_mainlines = []
    for line in mainlines:
        if line.endswith(utils.choice_close_delimiter):
            new_mainlines.append(randomize_choice(line))
        # elif utils.choice_open_delimiter in line or utils.choice_close_delimiter in line:
        #     print(line)
        else:
            new_mainlines.append(line)

    if False: # TODO: make this an option
        lines = prelines + keylines + new_mainlines + costlines + postlines
        random.shuffle(lines)
        return utils.newline.join(lines)
    else:
        random.shuffle(prelines)
        random.shuffle(keylines)
        random.shuffle(new_mainlines)
        random.shuffle(costlines)
        #random.shuffle(postlines) # only one kind ever (countertype)
        return utils.newline.join(prelines+keylines+new_mainlines+costlines+postlines)


# Text unpasses, for decoding. All assume the text inside a Manatext, so don't do anything
# weird with the mana cost symbol.


def text_unpass_1_choice(s, delimit = False):
    choice_regex = (re.escape(choice_open_delimiter) + re.escape(unary_marker)
                    + r'.*' + re.escape(bullet_marker) + r'.*' + re.escape(choice_close_delimiter))
    choices = re.findall(choice_regex, s)
    for choice in sorted(choices, lambda x,y: cmp(len(x), len(y)), reverse = True):
        fragments = choice[1:-1].split(bullet_marker)
        countfrag = fragments[0]
        optfrags = fragments[1:]
        choicecount = int(utils.from_unary(re.findall(utils.number_unary_regex, countfrag)[0]))
        newchoice = ''

        if choicecount == 0:
            if len(countfrag) == 2:
                newchoice += 'choose one or both '
            else:
                newchoice += 'choose one or more '
        elif choicecount == 1:
            newchoice += 'choose one '
        elif choicecount == 2:
            newchoice += 'choose two '
        else:
            newchoice += 'choose ' + utils.to_unary(str(choicecount)) + ' '
        newchoice += dash_marker
        
        for option in optfrags:
            option = option.strip()
            if option:
                newchoice += newline + bullet_marker + ' ' + option

        if delimit:
            s = s.replace(choice, choice_open_delimiter + newchoice + choice_close_delimiter)
            s = s.replace('an opponent ' + choice_open_delimiter + 'choose ', 
                          'an opponent ' + choice_open_delimiter + 'chooses ')
        else:
            s = s.replace(choice, newchoice)
            s = s.replace('an opponent choose ', 'an opponent chooses ')
    
    return s


def text_unpass_2_counters(s):
    countertypes = re.findall(r'countertype ' + re.escape(counter_marker) 
                              + r'[^' + re.escape(newline) + r']*' + re.escape(newline), s)
    # lazier than using groups in the regex
    countertypes += re.findall(r'countertype ' + re.escape(counter_marker) 
                              + r'[^' + re.escape(newline) + r']*$', s)
    if len(countertypes) > 0:
        countertype = countertypes[0].replace('countertype ' + counter_marker, '')
        countertype = countertype.replace(newline, '\n').strip()
        s = s.replace(countertypes[0], '')
        s = s.replace(counter_marker, countertype)
    
    return s


def text_unpass_3_uncast(s):
    return s.replace(counter_rename, 'counter')


def text_unpass_4_unary(s):
    return utils.from_unary(s)


def text_unpass_5_symbols(s, for_forum, for_html):
    return utils.from_symbols(s, for_forum = for_forum, for_html = for_html)


def text_unpass_6_cardname(s, name):
    return s.replace(this_marker, name)


def text_unpass_7_newlines(s):
    return s.replace(newline, '\n')


def text_unpass_8_unicode(s):
    s = s.replace(dash_marker, u'\u2014')
    s = s.replace(bullet_marker, u'\u2022')
    return s
