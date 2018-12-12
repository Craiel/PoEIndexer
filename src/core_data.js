const Constants = Object.freeze({
    'FPS': 30,
    'SettingsVersion': 1,
    'SettingsKey': 'POE_INDEXER_SETTINGS',
    'NinjaAPI': 'http://poe.ninja/api/Data/',
    'League': 'Betrayal',
    'ItemIgnoreFilter': [
        // Fragments of little to no value
        'Sacrifice at',
        'Divine Vessel',
        'Offering to the Goddess',

        // Low Tier essences
        'Whispering Essence',
        'Muttering Essence',
        'Weeping Essence',
        'Wailing Essence',
        'Screaming Essence',
        'Shrieking Essence'
    ],
    'EvalMinValue': 5,
    'EvalMinGrosGain': 5,
    'EvalMinGrosGainPc': 25
});

const ContentTypeEnum = Object.freeze({
    "Main": "content_main",
    "Settings": "content_settings",
    "Changelog": "content_changelog",
});

const ItemTypeEnum = Object.freeze({
    'Armor': 'UniqueArmour',
    'Weapon': 'UniqueWeapon',
    'Accessory': 'UniqueAccessory',
    'Fragment': 'Fragment',
    'Prophecy': 'Prophecy',
    'Gem': 'SkillGem',
    'Essence': 'Essence',
    'Card': 'DivinationCard',
    'Flask': 'UniqueFlask',
    'Jewel': 'UniqueJewel',
    'Map': 'UniqueMap',
    'Scarab': 'Scarab',
    'Fossil': 'Fossil',
    'Resonator': 'Resonator',
    'HelmetEnchant': 'HelmetEnchant',
    'BaseType': 'BaseType',

    // Currency last -> first to load
    'Currency': 'Currency'
});