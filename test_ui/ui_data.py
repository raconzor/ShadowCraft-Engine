# the following items had incorrect stats and should be corrected now
# necklace of strife
# wind dancer tunic
# dispersing belt
# storm rider's boots
# wind dancer gloves
# Uhn'agh Fash
# Poison Protocol Pauldrons
# Wind Dancer's Spaulders
# lots of necks/heads

import math

class Item(object):
    reforgable_stats = frozenset([
        'crit',
        'hit',
        'exp',
        'haste',
        'mastery'
    ])

    def __init__(self, name, id=0, str=0, agi=0, ap=0, crit=0, hit=0, exp=0, haste=0, mastery=0, sockets=[], bonus_stat='', bonus_value=0, proc='', gear_buff=''):
        self.name = name
        self.id = id
        self.str = str
        self.agi = agi
        self.ap = ap
        self.crit = crit
        self.hit = hit
        self.exp = exp
        self.haste = haste
        self.mastery = mastery
        self.sockets = sockets
        self.bonus_stat = bonus_stat
        self.bonus_value = bonus_value
        self.proc = proc
        self.gear_buff = gear_buff
    
    def reforgable_from(self):
        reforgable = []
        for stat in self.reforgable_stats:
            if getattr(self, stat) > 0:
                reforgable.append(stat)
        return reforgable
    
    def reforgable_to(self):
        reforgable = []
        for stat in self.reforgable_stats:
            if getattr(self, stat) == 0:
                reforgable.append(stat)
        return reforgable
    
    def reforge(self, from_stat, to_stat):
        print "before: " + from_stat + " = " + str(getattr(self, from_stat))
        print "        " + to_stat + " = " + str(getattr(self, to_stat))
        reforged_value = math.floor(getattr(self, from_stat) * 0.4)
        setattr(self, from_stat, getattr(self, from_stat) - reforged_value)
        setattr(self, to_stat, reforged_value)
        print "after: " + from_stat + " = " + str(getattr(self, from_stat))
        print "        " + to_stat + " = " + str(getattr(self, to_stat))

class Weapon(Item):
    def __init__(self, name, id=0, str=0, agi=0, ap=0, crit=0, hit=0, exp=0, haste=0, mastery=0, sockets=[], bonus_stat='', bonus_value=0, proc='', gear_buff='', damage=0, speed=0, type=''):
        super(Weapon, self).__init__(name, id, str, agi, ap, crit, hit, exp, haste, mastery, sockets, bonus_stat, bonus_value, proc, gear_buff)
        self.damage = damage
        self.speed = speed
        self.type = type

head = {
    #'Agile Bio-Optic Killshades': {'id': 59455, 'agi': 301, 'sockets': ['meta'], 'bonus_stat': 'agi', 'bonus_value': 20}, # missing cogwheels
    "(H)Membrane of C'Thun": {'id': 65129, 'agi': 325, 'exp': 197, 'haste': 257, 'sockets': ['yellow', 'meta'], 'bonus_stat': 'haste', 'bonus_value': 30},
    "Membrane of C'Thun": {'id': 59490, 'agi': 281, 'exp': 168, 'haste': 228, 'sockets': ['yellow', 'meta'], 'bonus_stat': 'haste', 'bonus_value': 30},
    "Tsanga's Helm": {'id': 60202, 'agi': 281, 'crit': 168, 'mastery': 228, 'sockets': ['blue', 'meta'], 'bonus_stat': 'agi', 'bonus_value': 30},
    "(H)Wind Dancer's Helmet": {'id': 65241, 'agi': 325, 'crit': 257, 'hit': 197, 'sockets': ['blue', 'meta'], 'bonus_stat': 'agi', 'bonus_value': 30, 'gear_buff': 'tier_11'}, # Tier 11
    "Wind Dancer's Helmet": {'id': 60299, 'agi': 281, 'crit': 228, 'hit': 168, 'sockets': ['blue', 'meta'], 'bonus_stat': 'agi', 'bonus_value': 30, 'gear_buff': 'tier_11'}, # Tier 11
    'Dunwald Winged Helm': {'id': 63833, 'agi': 268, 'haste': 178, 'mastery': 178},
    '(H)Helm of Numberless Shadows': {'id': 56344, 'agi': 242, 'crit': 162, 'hit': 182, 'sockets': ['blue', 'meta'], 'bonus_stat': 'agi', 'bonus_value': 30},
    'Helm of Secret Knowledge': {'id': 66936, 'agi': 208, 'crit': 117, 'haste': 171, 'sockets': ['yellow', 'meta'], 'bonus_stat': 'mastery', 'bonus_value': 30},
    'Hood of the Crying Rogue': {'id': 66975, 'agi': 208, 'crit': 117, 'haste': 171, 'sockets': ['yellow', 'meta'], 'bonus_stat': 'mastery', 'bonus_value': 30},
    'Mask of Vines': {'id': 58133, 'agi': 242, 'crit': 182, 'haste': 162, 'sockets': ['blue', 'meta'], 'bonus_stat': 'agi', 'bonus_value': 30},
    'Shocktrooper Hood': {'id': 63829, 'agi': 268, 'haste': 178, 'mastery': 178},
}
neck = {
    '(H)Necklace of Strife': {'id': 65107, 'agi': 215, 'haste': 143, 'mastery': 143},
    'Necklace of Strife': {'id': 59517, 'agi': 190, 'haste': 127, 'mastery': 127},
    'Acorn of the Daughter Tree': {'id': 62378, 'agi': 168, 'crit': 112, 'haste': 112},
    'Amulet of Dull Dreaming': {'id': 57931, 'agi': 168, 'crit': 112, 'haste': 112},
    '(H)Barnacle Pendant': {'id': 56292, 'agi': 168, 'exp': 120, 'haste': 98},
    'Brazen Elementium Medallion': {'id': 52350, 'agi': 138, 'crit': 112, 'exp': 102, 'sockets': ['red'], 'bonus_stat': 'str', 'bonus_value': 10}, # str socket
    'Entwined Elementium Choker': {'id': 52321, 'agi': 148, 'crit': 65, 'haste': 128, 'sockets': ['yellow'], 'bonus_stat': 'mastery', 'bonus_value': 10},
    '(H)Mouth of the Earth': {'id': 56422, 'agi': 168, 'hit': 112, 'exp': 112},
    'Mouth of the Earth': {'id': 56095, 'agi': 149, 'hit': 100, 'exp': 100},
    'Nightrend Choker': {'id': 66974, 'agi': 149, 'crit': 100, 'haste': 100},
    '(H)Pendant of the Lightless Grotto': {'id': 56338, 'agi': 168, 'crit': 112, 'mastery': 112},
    'Pendant of Victorious Fury': {'id': 63762, 'agi': 149, 'haste': 105, 'mastery': 90},
    'Sweet Perfume Broach': {'id': 68174, 'agi': 168, 'crit': 101, 'haste': 119},
}
shoulders = {
    '(H)Poison Protocol Pauldrons': {'id': 65083, 'agi': 226, 'crit': 171, 'mastery': 191, 'sockets': ['red'], 'bonus_stat': 'mastery', 'bonus_value': 10},
    'Poison Protocol Pauldrons': {'id': 59120, 'agi': 233, 'crit': 149, 'mastery': 169, 'sockets': ['red'], 'bonus_stat': 'mastery', 'bonus_value': 10},
    "(H)Wind Dancer's Spaulders": {'id': 65243, 'agi': 266, 'crit': 171, 'haste': 191, 'sockets': ['blue'], 'bonus_stat': 'agi', 'bonus_value': 10, 'gear_buff': 'tier_11'}, # Tier 11
    "Wind Dancer's Spaulders": {'id': 60302, 'agi': 233, 'crit': 149, 'haste': 169, 'sockets': ['blue'], 'bonus_stat': 'agi', 'bonus_value': 10, 'gear_buff': 'tier_11'}, # Tier 11
    '(H)Caridean Epaulettes': {'id': 56273, 'agi': 205, 'exp': 150, 'haste': 130, 'sockets': ['red'], 'bonus_stat': 'haste', 'bonus_value': 10},
    'Clandestine Spaulders': {'id': 66905, 'agi': 199, 'crit': 142, 'haste': 116},
    'Embrace of the Night': {'id': 58134, 'agi': 205, 'crit': 150, 'hit': 130, 'sockets': ['blue'], 'bonus_stat': 'agi', 'bonus_value': 10},
    '(H)Thieving Spaulders': {'id': 63449, 'agi': 205, 'crit': 130, 'haste': 150, 'sockets': ['yellow'], 'bonus_stat': 'haste', 'bonus_value': 20},
}
back = {
    '(H)Cloak of Biting Chill': {'id': 65035, 'agi': 215, 'crit': 143, 'mastery': 143},
    'Cloak of Biting Chill': {'id': 59348, 'agi': 190, 'crit': 127, 'mastery': 127},
    'Viewless Wings': {'id': 58191, 'agi': 190, 'crit': 127, 'hit': 127},
    '(H)Cape of the Brotherhood': {'id': 65177, 'agi': 168, 'hit': 112, 'haste': 112},
    'Cloak of Beasts': {'id': 56518, 'agi': 149, 'hit': 114, 'mastery': 76},
    '(H)Cloak of Thredd': {'id': 63473, 'agi': 168, 'crit': 112, 'mastery': 112},
    '(H)Kaleki Cloak': {'id': 56379, 'agi': 168, 'hit': 85, 'mastery': 128},
    'Kaleki Cloak': {'id': 55858, 'agi': 149, 'hit': 76, 'mastery': 114},
    'Razor-Edged Cloak': {'id': 56548, 'agi': 168, 'crit': 125, 'mastery': 90},
    'Softwind Cape': {'id': 62361, 'agi': 168, 'hit': 112, 'haste': 112},
    '(H)Twitching Shadows': {'id': 56315, 'agi': 168, 'crit': 112, 'haste': 112},
}
chest = {
    "Assassin's Chestplate": {'id': 56562, 'agi': 341, 'crit': 253, 'hit': 183},
    "Morrie's Waywalker Wrap": {'id': 67135, 'agi': 301, 'crit': 198, 'mastery': 218, 'sockets': ['red', 'yellow'], 'bonus_stat': 'mastery', 'bonus_value': 20},
    '(H)Sark of the Unwatched': {'id': 65060, 'agi': 345, 'crit': 227, 'mastery': 247,'sockets': ['red', 'yellow'], 'bonus_stat': 'mastery', 'bonus_value': 20},
    'Sark of the Unwatched': {'id': 59318, 'agi': 301, 'crit': 198, 'mastery': 218, 'sockets': ['red', 'yellow'], 'bonus_stat': 'mastery', 'bonus_value': 20},
    "(H)Wind Dancer's Tunic": {'id': 65239, 'agi': 345, 'exp': 217, 'haste': 257, 'sockets': ['red', 'blue'], 'bonus_stat': 'agi', 'bonus_value': 20, 'gear_buff': 'tier_11'}, # Tier 11
    "Wind Dancer's Tunic": {'id': 60301, 'agi': 301, 'exp': 188, 'haste': 228, 'sockets': ['red', 'blue'], 'bonus_stat': 'agi', 'bonus_value': 20, 'gear_buff': 'tier_11'}, # Tier 11
    '(H)Defias Brotherhood Vest': {'id': 63468, 'agi': 262, 'haste': 182, 'mastery': 182, 'sockets': ['red', 'yellow'], 'bonus_stat': 'mastery', 'bonus_value': 20},
    '(H)Hieroglyphic Vest': {'id': 57874, 'agi': 262, 'crit': 182, 'haste': 182, 'sockets': ['yellow', 'yellow'], 'bonus_stat': 'agi', 'bonus_value': 20},
    'Hieroglyphic Vest': {'id': 57863, 'agi': 228, 'crit': 158, 'haste': 158, 'sockets': ['yellow', 'yellow'], 'bonus_stat': 'agi', 'bonus_value': 20},
    'Sly Fox Jerkin': {'id': 62374, 'agi': 228, 'crit': 178, 'mastery': 138, 'sockets': ['red', 'blue'], 'bonus_stat': 'mastery', 'bonus_value': 20},
    'Tunic of Sinking Envy': {'id': 58131, 'agi': 262, 'crit': 202, 'hit': 162, 'sockets': ['red', 'blue'], 'bonus_stat': 'crit', 'bonus_value': 20},
    '(H)Vest of Misshapen Hides': {'id': 56455, 'agi': 262, 'crit': 162, 'mastery': 202, 'sockets': ['red', 'blue'], 'bonus_stat': 'mastery', 'bonus_value': 20},
    'Vest of Misshapen Hides': {'id': 56128, 'agi': 268, 'crit': 178, 'mastery': 178},

}
wrists = {
    '(H)Parasitic Bands': {'id': 65050, 'agi': 215, 'crit': 143, 'mastery': 143},
    'Parasitic Bands': {'id': 59329, 'agi': 190, 'crit': 127, 'mastery': 127},
    '(H)Double Dealing Bracers': {'id': 63454, 'agi': 168, 'crit': 112, 'mastery': 112},
    '(H)Poison Fang Bracers': {'id': 56409, 'agi': 168, 'hit': 112, 'haste': 112},
    'Poison Fang Bracers': {'id': 55886, 'agi': 149, 'hit': 100, 'haste': 100},
}
hands = {
    '(H)Double Attack Handguards': {'id': 65073, 'agi': 266, 'exp': 171, 'mastery': 191, 'sockets': ['red'], 'bonus_stat': 'mastery', 'bonus_value': 10},
    'Double Attack Handguards': {'id': 59223, 'agi': 233, 'exp': 149, 'mastery': 169, 'sockets': ['red'], 'bonus_stat': 'mastery', 'bonus_value': 10},
    "Liar's Handwraps": {'id': 62417, 'agi': 233, 'crit': 149, 'haste': 169, 'sockets': ['yellow'], 'bonus_stat': 'haste', 'bonus_value': 10},
    'Stormbolt Gloves': {'id': 62433, 'agi': 233, 'crit': 149, 'haste': 169, 'sockets': ['yellow'], 'bonus_stat': 'haste', 'bonus_value': 10},
    "(H)Wind Dancer's Gloves": {'id': 65240, 'agi': 266, 'hit': 171, 'haste': 191, 'sockets': ['red'], 'bonus_stat': 'haste', 'bonus_value': 10, 'gear_buff': 'tier_11'}, # Tier 11
    "Wind Dancer's Gloves": {'id': 60298, 'agi': 233, 'hit': 149, 'haste': 169, 'sockets': ['red'], 'bonus_stat': 'haste', 'bonus_value': 10, 'gear_buff': 'tier_11'}, # Tier 11
    '(H)Gloves of Haze': {'id': 56368, 'agi': 205, 'crit': 150, 'mastery': 130, 'sockets': ['blue'], 'bonus_stat': 'crit', 'bonus_value': 10},
    'Sticky Fingers': {'id': 58138, 'agi': 205, 'haste': 130, 'mastery': 150, 'sockets': ['yellow'], 'bonus_stat': 'agi', 'bonus_value': 10},
}
waist = {
    'Belt of Nefarious Whispers': {'id': 56537, 'agi': 253, 'hit': 184, 'mastery': 144, 'sockets': ['prismatic']},
    '(H)Dispersing Belt': {'id': 65122, 'agi': 266, 'crit': 171, 'haste': 191, 'sockets': ['blue', 'prismatic'], 'bonus_stat': 'agi', 'bonus_value': 10},
    'Dispersing Belt': {'id': 59502, 'agi': 233, 'crit': 149, 'haste': 169, 'sockets': ['blue', 'prismatic'], 'bonus_stat': 'agi', 'bonus_value': 10},
    'Belt of a Thousand Mouths': {'id': 67240, 'agi': 225, 'crit': 150, 'haste': 150, 'sockets': ['prismatic']},
    'Quicksand Belt': {'id': 62446, 'agi': 205, 'crit': 130, 'hit': 150, 'sockets': ['blue', 'prismatic'], 'bonus_stat': 'agi', 'bonus_value': 10},
    '(H)Red Beam Cord': {'id': 56429, 'agi': 205, 'crit': 130, 'hast': 150, 'sockets': ['blue', 'prismatic'], 'bonus_stat': 'haste', 'bonus_value': 10},
    'Red Beam Cord': {'id': 56098, 'agi': 199, 'crit': 133, 'haste': 133, 'sockets': ['blue', 'prismatic'], 'bonus_stat': 'haste', 'bonus_value': 10},
    'Sash of Musing': {'id': 57918, 'agi': 205, 'exp': 130, 'mastery': 150, 'sockets': ['red', 'prismatic'], 'bonus_stat': 'mastery', 'bonus_value': 10},
}
legs = {
    "(H)Aberration's Leggings": {'id': 65039, 'agi': 345, 'crit': 257, 'haste': 217, 'sockets': ['yellow', 'yellow'], 'bonus_stat': 'agi', 'bonus_value': 20},
    "Aberration's Leggings": {'id': 59343, 'agi': 301, 'crit': 228, 'haste': 188, 'sockets': ['yellow', 'yellow'], 'bonus_stat': 'agi', 'bonus_value': 20},
    "(H)Wind Dancer's Legguards": {'id': 65242, 'agi': 345, 'crit': 217, 'mastery': 257, 'sockets': ['yellow', 'blue'], 'bonus_stat': 'agi', 'bonus_value': 20, 'gear_buff': 'tier_11'}, # Tier 11
    "Wind Dancer's Legguards": {'id': 60300, 'agi': 301, 'crit': 188, 'mastery': 228, 'sockets': ['yellow', 'blue'], 'bonus_stat': 'agi', 'bonus_value': 20, 'gear_buff': 'tier_11'}, # Tier 11
    "(H)Beauty's Chew Toy": {'id': 56309, 'agi': 262, 'hit': 162, 'haste': 202, 'sockets': ['red', 'blue'], 'bonus_stat': 'haste', 'bonus_value': 20},
    "Garona's Finest Leggings": {'id': 63703, 'agi': 268, 'crit': 191, 'exp': 157},
    'Leggings of the Burrowing Mole': {'id': 58132, 'agi': 262, 'exp': 162, 'mastery': 202, 'sockets': ['red', 'blue'], 'bonus_stat': 'agi', 'bonus_value': 20},
    'Leggings of the Impenitent': {'id': 62405, 'agi': 228, 'crit': 168, 'haste': 148, 'sockets': ['red', 'yellow'], 'bonus_stat': 'crit', 'bonus_value': 20},
    "Shaw's Finest Leggings": {'id': 63707, 'agi': 268, 'crit': 191, 'exp': 157},
    'Swiftflight Leggings': {'id': 62425, 'agi': 228, 'crit': 168, 'haste': 148, 'sockets': ['red', 'yellow'], 'bonus_stat': 'crit', 'bonus_value': 20},
}
feet = {
    "(H)Storm Rider's Boots": {'id': 65144, 'agi': 266, 'haste': 171, 'mastery': 191, 'sockets': ['yellow'], 'bonus_stat': 'mastery', 'bonus_value': 10}, # not tagged heroic in wowhead
    "Storm Rider's Boots": {'id': 59469, 'agi': 233, 'haste': 149, 'mastery': 169, 'sockets': ['yellow'], 'bonus_stat': 'mastery', 'bonus_value': 10},
    'Treads of Fleeting Joy': {'id': 58482, 'agi': 233, 'crit': 149, 'haste': 169, 'sockets': ['blue'], 'bonus_stat': 'agi', 'bonus_value': 10},
    'Boots of the Hard Way': {'id': 66914, 'agi': 199, 'crit': 116, 'haste': 142},
    '(H)Boots of the Predator': {'id': 63435, 'agi': 205, 'crit': 150, 'hit': 130, 'sockets': ['yellow'], 'bonus_stat': 'crit', 'bonus_value': 10},
    "(H)Crafty's Gaiters": {'id': 56395, 'agi': 205, 'haste': 130, 'mastery': 150, 'sockets': ['blue'], 'bonus_stat': 'mastery', 'bonus_value': 10},
    "Crafty's Gaiters": {'id': 55871, 'agi': 199, 'haste': 133, 'mastery': 133},
    "(H)VanCleef's Boots": {'id': 65178, 'agi': 205, 'haste': 150, 'mastery': 130, 'sockets': ['yellow'], 'bonus_stat': 'agi', 'bonus_value': 10},
}
rings = {
    'Gilnean Ring of Ruination': {'id': 67136, 'agi': 190, 'hit': 108, 'haste': 138},
    '(H)Lightning Conductor Band': {'id': 65082, 'agi': 215, 'crit': 143, 'hit': 143},
    'Lightning Conductor Band': {'id': 59121, 'agi': 190, 'crit': 127, 'hit': 127},
    'Signet of the Elder Council': {'id': 62362, 'agi': 190, 'haste': 127, 'mastery': 127},
    'Band of Blades': {'id': 52318, 'agi': 138, 'crit': 116, 'hit': 97, 'sockets': ['yellow'], 'bonus_stat': 'hit', 'bonus_value': 10},
    "Elementium Destroyer's Ring": {'id': 52348, 'agi': 148, 'crit': 89, 'mastery': 114, 'sockets': ['red'], 'bonus_stat': 'haste', 'bonus_value': 10},
    '(H)Mirage Ring': {'id': 56404, 'agi': 168, 'hit': 85, 'haste': 128},
    'Mirage Ring': {'id': 55884, 'agi': 149, 'hit': 76, 'haste': 114},
    '(H)Nautilus Ring': {'id': 56282, 'agi': 168, 'crit': 112, 'haste': 112},
    '(H)Ring of Blinding Stars': {'id': 56412, 'agi': 168, 'haste': 112, 'mastery': 112},
    'Ring of Blinding Stars': {'id': 55994, 'agi': 149, 'haste': 100, 'mastery': 100},
    '(H)Ring of Dun Algaz': {'id': 56445, 'agi': 168, 'crit': 120, 'hit': 98},
    'Ring of Dun Algaz': {'id': 56120, 'agi': 149, 'crit': 107, 'hit': 87},
    '(H)Skullcracker Ring': {'id': 58186, 'agi': 168, 'crit': 112, 'haste': 112},
    '(H)Skullcracker Ring': {'id': 56310, 'agi': 168, 'crit': 112, 'mastery': 112},
    "Terrath's Signet of Balance": {'id': 62348, 'agi': 168, 'hit': 112, 'mastery': 112},
}
ring1 = rings
ring2 = rings
trinkets = {
    '(H)Grace of the Herald': {'id': 56295, 'agi': 285, 'proc': 'heroic_grace_of_the_herald'},
    'Grace of the Herald': {'id': 55266, 'agi': 153, 'proc': 'grace_of_the_herald'},
    '(H)Key to the Endless Chamber': {'id': 56328, 'hit': 285, 'proc': 'heroic_key_to_the_endless_chamber'},
    'Key to the Endless Chamber': {'id': 55795, 'hit': 215, 'proc': 'key_to_the_endless_chamber'},
    '(H)Left Eye of Rajh': {'id': 56427, 'exp': 285, 'proc': 'heroic_left_eye_of_rajh'},
    'Left Eye of Rajh': {'id': 56102, 'exp': 252, 'proc': 'left_eye_of_rajh'},
    "(H)Prestor's Talisman of Machination": {'id': 65026, 'agi': 363, 'proc': 'heroic_prestors_talisman_of_machination'},
    "Prestor's Talisman of Machination": {'id': 59441, 'agi': 321, 'proc': 'prestors_talisman_of_machination'},
    "(H)Tia's Grace": {'id': 56394, 'mastery': 285, 'proc': 'heroic_tias_grace'},
    "Tia's Grace": {'id': 55874, 'mastery': 252, 'proc': 'tias_grace'},
    'Darkmoon Card: Hurricane ': {'id': 62051, 'agi': 321, 'proc': 'darkmoon_card_hurricane'},
    'Essence of the Cyclone': {'id': 59473, 'agi': 321, 'proc': 'essence_of_the_cyclone'},
    'Fluid Death ': {'id': 58181, 'hit': 321, 'proc': 'fluid_death'},
    'Heart of the Vile': {'id': 66969, 'agi': 234, 'proc': 'heart_of_the_vile'},
    'Unheeded Warning ': {'id': 59520, 'agi': 321, 'proc': 'unheeded_warning'},
    'Unsolvable Riddle': {'id': 62463, 'mastery': 321, 'gear_buff': 'unsolvable_riddle'},
    'Figurine - Demon Panther ': {'id': 52199, 'hit': 285, 'gear_buff': 'demon_panther '},
}
trinket1 = trinkets
trinket2 = trinkets
melee_weapons = {
    '1.8d (H)Organic Lifeform Inverter': {'id': 65081, 'agi': 165, 'exp': 110, 'mastery': 110, 'damage': 939.5, 'speed': 1.8, 'type': 'dagger'},
    '1.8d Organic Lifeform Inverter': {'id': 59122, 'agi': 146, 'exp': 97, 'mastery': 97, 'damage': 832, 'speed': 1.8, 'type': 'dagger'},
    '1.4d Scaleslicer': {'id': 68601, 'agi': 146, 'hit': 97, 'exp': 97, 'damage': 647.5, 'speed': 1.4, 'type': 'dagger'},
    '1.8d The Twilight Blade': {'id': 68163, 'proc': 'the_twilight_blade', 'damage': 832, 'speed': 1.8, 'type': 'dagger'},
    "1.4d (H)Uhn'agh Fash, the Darkest Betrayal": {'id': 68600, 'agi': 165, 'crit': 110, 'haste': 110, 'damage': 750.5, 'speed': 1.4, 'type': 'dagger'},
    "1.4d Uhn'agh Fash, the Darkest Betrayal": {'id': 59494, 'agi': 146, 'crit': 97, 'haste': 97, 'damage': 647.5, 'speed': 1.4, 'type': 'dagger'},
    "1.4d (H)Barim's Main Gauche": {'id': 56390, 'agi': 129, 'crit': 86, 'mastery': 86, 'damage': 573.5, 'speed': 1.4, 'type': 'dagger'},
    "1.4d Barim's Main Gauche": {'id': 55870, 'agi': 115, 'crit': 76, 'mastery': 76, 'damage': 508, 'speed': 1.4, 'type': 'dagger'},
    '1.4d (H)Buzzer Blade': {'id': 65163, 'agi': 129, 'crit': 86, 'haste': 86, 'damage': 573.5, 'speed': 1.4, 'type': 'dagger'},
    '1.8d Dagger of Restless Nights': {'id': 62456, 'agi': 129, 'crit': 86, 'hit': 86, 'damage': 737, 'speed': 1.8, 'type': 'dagger'},
    '1.8d Elementium Shank': {'id': 55068, 'agi': 129, 'hit': 86, 'haste': 86, 'damage': 737.5, 'speed': 1.8, 'type': 'dagger'},
    '1.8d Laquered Lung-Leak Longknife': {'id': 63792, 'agi': 115, 'crit': 75, 'mastery': 78, 'damage': 653.5, 'speed': 1.8, 'type': 'dagger'},
    #'1.8d (H)Meteor Shard': {'id': 63456, 'agi': 129, 'damage': 737.5, 'speed': 1.8, 'type': 'dagger'}, # not modeled proc
    '1.4d (H)Quicksilver Blade': {'id': 56335, 'agi': 129, 'haste': 86, 'mastery': 86, 'damage': 573.5, 'speed': 1.4, 'type': 'dagger'},
    "1.8d (H)Steelbender's Masterpiece": {'id': 56302, 'agi': 129, 'hit': 93, 'mastery': 76, 'damage': 737, 'speed': 1.8, 'type': 'dagger'},
    '1.4d Throat Slasher': {'id': 57927, 'agi': 129, 'crit': 86, 'hit': 86, 'damage': 573.5, 'speed': 1.4, 'type': 'dagger'}, # off hand
    '1.4d (H)Toxidunk Dagger': {'id': 56326, 'agi': 129, 'hit': 86, 'exp': 86, 'damage': 573.5, 'speed': 1.4, 'type': 'dagger'},
    '1.8d (H)Wicked Dagger': {'id': 63477, 'agi': 129, 'crit': 86, 'exp': 86, 'damage': 737.5, 'speed': 1.8, 'type': 'dagger'},
    '1.8d (H)Windwalker Blade': {'id': 56454, 'agi': 129, 'crit': 86, 'exp': 86, 'damage': 737, 'speed': 1.8, 'type': 'dagger'},
    '1.8d Windwalker Blade': {'id': 56127, 'agi': 115, 'crit': 76, 'exp': 76, 'damage': 653, 'speed': 1.8, 'type': 'dagger'},
    '2.6f (H)Claws of Torment': {'id': 65006, 'agi': 165, 'crit': 110, 'haste': 110, 'damage': 1356.5, 'speed': 2.6, 'type': 'fist'}, # main hand
    '2.6f Claws of Torment': {'id': 63537, 'agi': 146, 'crit': 97, 'haste': 97, 'damage': 1202, 'speed': 2.6, 'type': 'fist'}, # main hand
    '2.6f Crystalline Geoknife': {'id': 66972, 'agi': 115, 'crit': 76, 'haste': 76, 'damage': 943.5, 'speed': 2.6, 'type': 'fist'}, # main hand
    '2.6f (H)Fist of Pained Senses': {'id': 56329, 'agi': 129, 'crit': 86, 'haste': 86, 'damage': 1065, 'speed': 2.6, 'type': 'fist'}, # main hand
    '2.6f The Perforator': {'id': 52493, 'agi': 95, 'crit': 87, 'mastery': 38, 'sockets': ['red'], 'bonus_stat': 'mastery', 'bonus_value': 10, 'damage': 943.5, 'speed': 2.6, 'type': 'fist'},
    "2.6a (H)Crul'korak, the Lightning's Arc": {'id': 65024, 'agi': 165, 'crit': 110, 'haste': 110, 'damage': 1356.5, 'speed': 2.6, 'type': 'axe'},
    "2.6a Crul'korak, the Lightning's Arc": {'id': 59443, 'agi': 146, 'crit': 97, 'haste': 97, 'damage': 1202, 'speed': 2.6, 'type': 'axe'},
    # "2.6a (H)Maimgor's Bite": {'id': 65014, 'agi': 165, 'hit': 110, 'mastery': 110, 'damage': 1356.5, 'speed': 2.6, 'type': 'axe'}, # off hand
    # "2.6a Maimgor's Bite": {'id': 59462, 'agi': 146, 'hit': 97, 'mastery': 97, 'damage': 1202, 'speed': 2.6, 'type': 'axe'}, # off hand
    "2.6a Calder's Coated Carrion Carver": {'id': 63788, 'agi': 115, 'crit': 84, 'haste': 63, 'damage': 943.5, 'speed': 2.6, 'type': 'axe'},
    '2.6a Elementium Gutslicer': {'id': 67602, 'agi': 129, 'hit': 86, 'mastery': 86, 'damage': 1065, 'speed': 2.6, 'type': 'axe'},
    '2.6a (H)Lightning Whelk Axe': {'id': 56266, 'agi': 129, 'crit': 86, 'hit': 86, 'damage': 1065, 'speed': 2.6, 'type': 'axe'},
    '2.6a Ravening Slicer': {'id': 62457, 'agi': 129, 'haste': 86, 'mastery': 86, 'damage': 1065, 'speed': 2.6, 'type': 'axe'},
    # '2.6a Windslicer': {'id': Windslicer, 'agi': 129, 'crit': 86, 'mastery': 86, 'damage': 1065, 'speed': 2.6, 'type': 'axe'}, # off hand
    '2.6m (H)Hammer of Sparks': {'id': 56396, 'agi': 129, 'crit': 86, 'hit': 86, 'damage': 1065, 'speed': 2.6, 'type': 'mace'},
    '2.6m Hammer of Sparks': {'id': 55875, 'agi': 115, 'crit': 76, 'hit': 76, 'damage': 943.5, 'speed': 2.6, 'type': 'mace'},
    '2.6m (H)Heavy Geode Mace': {'id': 56353, 'agi': 129, 'hit': 86, 'exp': 86, 'damage': 1065, 'speed': 2.6, 'type': 'mace'},
    '2.6s (H)Fang of Twilight': {'id': 65094, 'agi': 165, 'crit': 110, 'mastery': 110, 'damage': 1356.5, 'speed': 2.6, 'type': 'sword'},
    '2.6s Fang of Twilight': {'id': 63533, 'agi': 146, 'crit': 97, 'mastery': 97, 'damage': 1202, 'speed': 2.6, 'type': 'sword'},
    '2.6s Krol Decapitator': {'id': 68161, 'agi': 146, 'hit': 86, 'haste': 105, 'damage': 1202, 'speed': 2.6, 'type': 'sword'},
    '2.7s (H)Cruel Barb': {'id': 65164, 'agi': 129, 'crit': 86, 'hit': 86, 'damage': 1106, 'speed': 2.7, 'type': 'sword'},
    "2.6s (H)Thief's Blade": {'id': 65173, 'agi': 129, 'haste': 86, 'mastery': 86, 'damage': 1065, 'speed': 2.6, 'type': 'sword'},
}
mainhand = melee_weapons
offhand = melee_weapons
ranged = {
    'Dragonwreck Throwing Axe': {'id': 68608, 'agi': 107, 'exp': 72, 'mastery': 72, 'damage': 1371.5, 'speed': 2.2, 'type': 'thrown'},
    'Spinerender': {'id': 68162, 'agi': 107, 'crit': 72, 'hit': 72, 'damage': 1371.5, 'speed': 2.2, 'type': 'thrown'},
    '(H)Slashing Thorns': {'id': 56420, 'agi': 95, 'crit': 63, 'hit': 63, 'damage': 1104.5, 'speed': 2, 'type': 'thrown'},
    'Slashing Thorns': {'id': 56001, 'agi': 84, 'crit': 56, 'hit': 56, 'damage': 978.5, 'speed': 2, 'type': 'thrown'},

}

default_talents = {
    'coup_de_grace': 3,
    'lethality': 3,
    'ruthlessness': 3,
    'quickening': 2,
    'puncturing_wounds': 3,
    'cold_blood': 1,
    'vile_poisons': 3,
    'deadened_nerves': 1,
    'seal_fate': 2,
    'murderous_intent': 2,
    'overkill': 1,
    'master_poisoner': 1,
    'cut_to_the_chase': 3,
    'venomous_wounds': 2,
    'vendetta': 1,
    'precision': 2,
    'nightstalker': 2,
    'relentless_strikes': 3,
    'opportunity': 3
}

enchants = {
    'head': {'Arcanum of the Ramkahen':{'agi': 60, 'haste': 35}},
    'shoulders': {
        'Greater Inscription of Shattered Crystal': {'agi': 50, 'mastery': 25},
        'Lesser Inscription of Shattered Crystal': {'agi': 30, 'mastery': 20}
    },
    'back': {
        'Greater Critical Strike': {'crit': 65},
        'Major Agility': {'agi': 22}
    },
    'chest': {'Peerless Stats': {'agi': 20, 'str': 20}},
    'wrists': {
        'Greater Speed': {'haste': 50},
        'Greater Expertise': {'exp': 50},
        'Precision': {'hit': 50},
        '(LW)Draconic Embossment':{'agi': 130}
    },
    'hands': {
        'Greater Mastery':{'mastery': 65},
        'Greater Expertise': {'exp': 50},
        'Haste': {'haste': 50}
    },
    'legs': {'Dragonbone': {'ap': 190, 'crit': 55}},
    'feet': {
        'Major Agility': {'agi': 35},
        'Mastery':{'mastery': 50},
        'Precision': {'hit': 50},
        'Haste': {'haste': 50}
    },
    'rings': {'dummy1': {}},
    'melee_weapons': {
        'Landslide': 'landslide',
        'Hurricane': 'hurricane'
    }
}

gems = {
    "Destructive Shadowspirit Diamond": (['meta'], {'crit': 54}),
    "Chaotic Shadowspirit Diamond": (['meta'], {'crit': 54, 'gear_buff': ['chaotic_metagem']}),
    "Delicate Chimera's Eye": (['red'], {'agi': 67}),
    "Delicate Inferno Ruby": (['red'], {'agi': 40}),
    "Adept Ember Topaz": (['red', 'yellow'], {'agi': 20, 'mastery': 20}),
    "Deft Ember Topaz": (['red', 'yellow'], {'agi': 20, 'haste': 20}),
    "Glinting Demonseye": (['red', 'blue'], {'agi': 20, 'hit': 20}),
    "Rigid Ocean Sapphire": (['blue'], {'hit': 40})
}