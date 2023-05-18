from pydantic import BaseModel

from app.enums import Campaigns


class CampaignConfig(BaseModel):
    countries_list: list
    columns_to_display_in_excerpt: list
    category_hierarchy: dict


def get_campaign_config(campaign: str) -> CampaignConfig:
    if campaign == Campaigns.what_women_want:
        config = CampaignConfig(
            countries_list=[('CM', 'Cameroon', 'Cameroonian'),
                            ('IN', 'India', 'Indian'),
                            ('KE', 'Kenya', 'Kenyan'),
                            ('MW', 'Malawi', 'Malawian'),
                            ('MX', 'Mexico', 'Mexican'),
                            ('NG', 'Nigeria', 'Nigerian'),
                            ('PK', 'Pakistan', 'Pakistani'),
                            ('TZ', 'Tanzania', 'Tanzanian'),
                            ('UG', 'Uganda', 'Ugandan'),
                            ('ZW', 'Zimbabwe', 'Zimbabwean')],
            columns_to_display_in_excerpt=[
                {"name": "Response", "id": "raw_response", "type": "text"},
                {"name": "Topic(s)", "id": "description", "type": "text"},
                {"name": "Country", "id": "canonical_country", "type": "text"},
                {"name": "Age", "id": "age_str", "type": "text"},
            ],
            category_hierarchy={
                "NA": {
                    "BETTERFACILITIES": "Increased, fully functional and closer health facilities",
                    "FREE": "Free and affordable care",
                    "HEALTH": "General health and health services",
                    "HEALTHPROFESSIONALS": "Increased, competent, and better supported health workers",
                    "INFORMATION": "Counseling, information and awareness",
                    "OTHERNONDETERMINABLE": "All other requests",
                    "POWER": "Power, rights, economic and gender equality",
                    "RESPECTFULCARE": "Respectful, dignified, non-discriminatory care",
                    "SEXUALREPRODUCTIVEHEALTH": "Sexual, reproductive, maternal, labor, postnatal and newborn health services",
                    "SUPPLIES": "Medicines and supplies",
                }
            },
        )

        return config

    elif campaign == Campaigns.what_young_people_want:
        config = CampaignConfig(
            countries_list=[('AF', 'Afghanistan', 'Afghan'),
                            ('AL', 'Albania', 'Albanian'),
                            ('DZ', 'Algeria', 'Algerian'),
                            ('AS', 'American Samoa', 'American Samoan'),
                            ('AD', 'Andorra', 'Andorran'),
                            ('AO', 'Angola', 'Angolan'),
                            ('AI', 'Anguilla', 'Anguillan'),
                            ('AQ', 'Antarctica', 'Antarctic'),
                            ('AG', 'Antigua and Barbuda', 'Antiguan and Barbudan'),
                            ('AR', 'Argentina', 'Argentinean'),
                            ('AM', 'Armenia', 'Armenian'),
                            ('AW', 'Aruba', 'Aruban'),
                            ('AU', 'Australia', 'Australian'),
                            ('AT', 'Austria', 'Austrian'),
                            ('AZ', 'Azerbaijan', 'Azerbaijani'),
                            ('BS', 'Bahamas', 'Bahamian'),
                            ('BH', 'Bahrain', 'Bahraini'),
                            ('BD', 'Bangladesh', 'Bangladeshi'),
                            ('BB', 'Barbados', 'Barbadian'),
                            ('BY', 'Belarus', 'Belarusian'),
                            ('BE', 'Belgium', 'Belgian'),
                            ('BZ', 'Belize', 'Belizean'),
                            ('BJ', 'Benin', 'Beninese'),
                            ('BM', 'Bermuda', 'Bermudan'),
                            ('BT', 'Bhutan', 'Bhutanese'),
                            ('BO', 'Bolivia', 'Bolivian'),
                            ('BQ', 'Bonaire', 'Bonaire Dutch'),
                            ('BA', 'Bosnia and Herzegovina', 'Bosnian'),
                            ('BW', 'Botswana', 'Motswana'),
                            ('BV', 'Bouvet Island', 'Bouvet Islander'),
                            ('BR', 'Brazil', 'Brazilian'),
                            ('IO', 'British Indian Ocean Territory', 'British'),
                            ('VG', 'British Virgin Islands', 'British Virgin Islander'),
                            ('BN', 'Brunei', 'Bruneian'),
                            ('BG', 'Bulgaria', 'Bulgarian'),
                            ('BF', 'Burkina Faso', 'Burkinabe'),
                            ('BI', 'Burundi', 'Burundian'),
                            ('CV', 'Cabo Verde', 'Cabo Verdean'),
                            ('KH', 'Cambodia', 'Cambodian'),
                            ('CM', 'Cameroon', 'Cameroonian'),
                            ('CA', 'Canada', 'Canadian'),
                            ('KY', 'Cayman Islands', 'Caymanian'),
                            ('CF', 'Central African Republic', 'Central African'),
                            ('TD', 'Chad', 'Chadian'),
                            ('CL', 'Chile', 'Chilean'),
                            ('CN', 'China', 'Chinese'),
                            ('CX', 'Christmas Island', 'Christmas Islander'),
                            ('CC', 'Cocos Islands', 'Cocos Islander'),
                            ('CO', 'Colombia', 'Colombian'),
                            ('KM', 'Comoros', 'Comoran'),
                            ('CK', 'Cook Islands', 'Cook Islander'),
                            ('CR', 'Costa Rica', 'Costa Rican'),
                            ('HR', 'Croatia', 'Croatian'),
                            ('CU', 'Cuba', 'Cuban'),
                            ('CW', 'Curaçao', 'Curaçaoan'),
                            ('CY', 'Cyprus', 'Cypriot'),
                            ('CZ', 'Czech Republic', 'Czech'),
                            ('CI', "Côte d'Ivoire", 'Ivorian'),
                            ('DK', 'Denmark', 'Danish'),
                            ('DJ', 'Djibouti', 'Djiboutian'),
                            ('DM', 'Dominica', 'Dominican'),
                            ('DO', 'Dominican Republic', 'Dominican'),
                            ('EC', 'Ecuador', 'Ecuadorean'),
                            ('EG', 'Egypt', 'Egyptian'),
                            ('SV', 'El Salvador', 'Salvadoran'),
                            ('GQ', 'Equatorial Guinea', 'Equatorial Guinean'),
                            ('ER', 'Eritrea', 'Eritrean'),
                            ('EE', 'Estonia', 'Estonian'),
                            ('SZ', 'Eswatini', 'Swazi'),
                            ('ET', 'Ethiopia', 'Ethiopian'),
                            ('FK', 'Falkland Islands', 'Falkland Islander'),
                            ('FO', 'Faroe Islands', 'Faroese'),
                            ('FJ', 'Fiji', 'Fijian'),
                            ('FI', 'Finland', 'Finnish'),
                            ('FR', 'France', 'French'),
                            ('GF', 'French Guiana', 'French Guianese'),
                            ('PF', 'French Polynesia', 'French Polynesian'),
                            ('TF', 'French Southern Territories', 'French Southern Territories'),
                            ('GA', 'Gabon', 'Gabonese'),
                            ('GM', 'Gambia', 'Gambian'),
                            ('DE', 'Germany', 'German'),
                            ('GH', 'Ghana', 'Ghanaian'),
                            ('GI', 'Gibraltar', 'Gibraltarian'),
                            ('GR', 'Greece', 'Greek'),
                            ('GL', 'Greenland', 'Greenlander'),
                            ('GD', 'Grenada', 'Grenadian'),
                            ('GP', 'Guadeloupe', 'Guadeloupian'),
                            ('GU', 'Guam', 'Guamanian'),
                            ('GT', 'Guatemala', 'Guatemalan'),
                            ('GG', 'Guernsey', 'Guernsey'),
                            ('GN', 'Guinea', 'Guinean'),
                            ('GW', 'Guinea-Bissau', 'Bissau-Guinean'),
                            ('GY', 'Guyana', 'Guyanese'),
                            ('HT', 'Haiti', 'Haitian'),
                            ('HM', 'Heard Island and McDonald Islands', 'Heard and McDonald Islander'),
                            ('HN', 'Honduras', 'Honduran'),
                            ('HK', 'Hong Kong', 'Hong Kong'),
                            ('HU', 'Hungary', 'Hungarian'),
                            ('IS', 'Iceland', 'Icelander'),
                            ('IN', 'India', 'Indian'),
                            ('ID', 'Indonesia', 'Indonesian'),
                            ('IR', 'Iran, Islamic Republic of', 'Iranian'),
                            ('IQ', 'Iraq', 'Iraqi'),
                            ('IE', 'Ireland', 'Irish'),
                            ('IM', 'Isle of Man', 'Manx'),
                            ('IL', 'Israel', 'Israeli'),
                            ('IT', 'Italy', 'Italian'),
                            ('JM', 'Jamaica', 'Jamaican'),
                            ('JP', 'Japan', 'Japanese'),
                            ('JE', 'Jersey', 'Jersey'),
                            ('JO', 'Jordan', 'Jordanian'),
                            ('KZ', 'Kazakhstan', 'Kazakhstani'),
                            ('KE', 'Kenya', 'Kenyan'),
                            ('KI', 'Kiribati', 'I-Kiribati'),
                            ('RS', 'Kosovo', 'Kosovar'),
                            ('KW', 'Kuwait', 'Kuwaiti'),
                            ('KG', 'Kyrgyzstan', 'Kyrgyzstani'),
                            ('LA', 'Laos', 'Laotian'),
                            ('LV', 'Latvia', 'Latvian'),
                            ('LB', 'Lebanon', 'Lebanese'),
                            ('LS', 'Lesotho', 'Mosotho'),
                            ('LR', 'Liberia', 'Liberian'),
                            ('LY', 'Libya', 'Libyan'),
                            ('LI', 'Liechtenstein', 'Liechtensteiner'),
                            ('LT', 'Lithuania', 'Lithuanian'),
                            ('LU', 'Luxembourg', 'Luxembourger'),
                            ('MG', 'Madagascar', 'Madagascan'),
                            ('MW', 'Malawi', 'Malawian'),
                            ('MY', 'Malaysia', 'Malaysian'),
                            ('MV', 'Maldives', 'Maldivian'),
                            ('ML', 'Mali', 'Malian'),
                            ('MT', 'Malta', 'Maltese'),
                            ('MH', 'Marshall Islands', 'Marshallese'),
                            ('MQ', 'Martinique', 'Martiniquais'),
                            ('MR', 'Mauritania', 'Mauritanian'),
                            ('MU', 'Mauritius', 'Mauritian'),
                            ('YT', 'Mayotte', 'Mahoran'),
                            ('MX', 'Mexico', 'Mexican'),
                            ('FM', 'Micronesia', 'Micronesian'),
                            ('MD', 'Moldova', 'Moldovan'),
                            ('MC', 'Monaco', 'Monégasque'),
                            ('MN', 'Mongolia', 'Mongolian'),
                            ('ME', 'Montenegro', 'Montenegrin'),
                            ('MS', 'Montserrat', 'Montserratian'),
                            ('MA', 'Morocco', 'Moroccan'),
                            ('MZ', 'Mozambique', 'Mozambican'),
                            ('MM', 'Myanmar', 'Myanmar'),
                            ('NA', 'Namibia', 'Namibian'),
                            ('NR', 'Nauru', 'Nauruan'),
                            ('NP', 'Nepal', 'Nepalese'),
                            ('NL', 'Netherlands', 'Dutch'),
                            ('NC', 'New Caledonia', 'New Caledonian'),
                            ('NZ', 'New Zealand', 'New Zealander'),
                            ('NI', 'Nicaragua', 'Nicaraguan'),
                            ('NE', 'Niger', 'Nigerien'),
                            ('NG', 'Nigeria', 'Nigerian'),
                            ('NU', 'Niue', 'Niuean'),
                            ('NF', 'Norfolk Island', 'Norfolk Islander'),
                            ('KP', 'North Korea', 'North Korean'),
                            ('MK', 'North Macedonia', 'Macedonian'),
                            ('MP', 'Northern Mariana Islands', 'Northern Marianan'),
                            ('NO', 'Norway', 'Norwegian'),
                            ('OM', 'Oman', 'Omani'),
                            ('PK', 'Pakistan', 'Pakistani'),
                            ('PW', 'Palau', 'Palauan'),
                            ('PS', 'Palestine', 'Palestinian'),
                            ('PA', 'Panama', 'Panamanian'),
                            ('PG', 'Papua New Guinea', 'Papua New Guinean'),
                            ('PY', 'Paraguay', 'Paraguayan'),
                            ('PE', 'Peru', 'Peruvian'),
                            ('PH', 'Philippines', 'Filipino'),
                            ('PN', 'Pitcairn Islands', 'Pitcairn Islander'),
                            ('PL', 'Poland', 'Polish'),
                            ('PT', 'Portugal', 'Portuguese'),
                            ('PR', 'Puerto Rico', 'Puerto Rican'),
                            ('QA', 'Qatar', 'Qatari'),
                            ('CG', 'Republic of the Congo', 'Congolese'),
                            ('RO', 'Romania', 'Romanian'),
                            ('RU', 'Russia[m]', 'Russian'),
                            ('RW', 'Rwanda', 'Rwandan'),
                            ('RE', 'Réunion', 'Réunionese'),
                            ('BL', 'Saint Barthélemy', 'Barthélemois'),
                            ('SH', 'Saint Helena, Ascension and Tristan da Cunha', 'Saint Helenian'),
                            ('KN', 'Saint Kitts and Nevis', 'Kittian and Nevisian'),
                            ('LC', 'Saint Lucia', 'Saint Lucian'),
                            ('MF', 'Saint Martin', 'Saint-Martinois'),
                            ('PM', 'Saint Pierre and Miquelon', 'Saint-Pierrais-Miquelonnais'),
                            ('VC', 'Saint Vincent and the Grenadines', 'Saint Vincentian'),
                            ('WS', 'Samoa', 'Samoan'),
                            ('SM', 'San Marino', 'Sammarinese'),
                            ('SA', 'Saudi Arabia', 'Saudi Arabian'),
                            ('SN', 'Senegal', 'Senegalese'),
                            ('SC', 'Seychelles', 'Seychellois'),
                            ('SL', 'Sierra Leone', 'Sierra Leonean'),
                            ('SG', 'Singapore', 'Singaporean'),
                            ('SX', 'Sint Maarten', 'Sint Maartener'),
                            ('SK', 'Slovakia', 'Slovak'),
                            ('SI', 'Slovenia', 'Slovene'),
                            ('SB', 'Solomon Islands', 'Solomon Islander'),
                            ('SO', 'Somalia', 'Somali'),
                            ('ZA', 'South Africa', 'South African'),
                            ('GS',
                             'South Georgia and the South Sandwich Islands',
                             'South Georgia and South Sandwich Islander'),
                            ('KR', 'South Korea', 'South Korean'),
                            ('SS', 'South Sudan', 'South Sudanese'),
                            ('ES', 'Spain', 'Spanish'),
                            ('LK', 'Sri Lanka', 'Sri Lankan'),
                            ('SD', 'Sudan', 'Sudanese'),
                            ('SR', 'Suriname', 'Surinamer'),
                            ('SE', 'Sweden', 'Swedish'),
                            ('CH', 'Switzerland', 'Swiss'),
                            ('SY', 'Syria', 'Syrian'),
                            ('TW', 'Taiwan[n]', 'Taiwanese'),
                            ('TJ', 'Tajikistan', 'Tajikistani'),
                            ('TZ', 'Tanzania, United Republic of', 'Tanzanian'),
                            ('TH', 'Thailand', 'Thai'),
                            ('CD', 'The Democratic Republic of the Congo', 'DRC Congolese'),
                            ('TL', 'Timor-Leste', 'East Timorese'),
                            ('TG', 'Togo', 'Togolese'),
                            ('TK', 'Tokelau', 'Tokelauan'),
                            ('TO', 'Tonga', 'Tongan'),
                            ('TT', 'Trinidad and Tobago', 'Trinidadian'),
                            ('TN', 'Tunisia', 'Tunisian'),
                            ('TR', 'Turkey', 'Turkish'),
                            ('TM', 'Turkmenistan', 'Turkmen'),
                            ('TC', 'Turks and Caicos Islands', 'Turks and Caicos Islander'),
                            ('TV', 'Tuvalu', 'Tuvaluan'),
                            ('UG', 'Uganda', 'Ugandan'),
                            ('UA', 'Ukraine', 'Ukrainian'),
                            ('AE', 'United Arab Emirates', 'Emirati'),
                            ('GB', 'United Kingdom', 'British'),
                            ('US', 'United States', 'American'),
                            ('UY', 'Uruguay', 'Uruguayan'),
                            ('UZ', 'Uzbekistan', 'Uzbekistani'),
                            ('VU', 'Vanuatu', 'Ni-Vanuatu'),
                            ('VE', 'Venezuela', 'Venezuelan'),
                            ('VN', 'Vietnam', 'Vietnamese'),
                            ('WF', 'Wallis and Futuna', 'Wallis and Futuna Islander'),
                            ('EH', 'Western Sahara', 'Sahrawi'),
                            ('YE', 'Yemen', 'Yemeni'),
                            ('ZM', 'Zambia', 'Zambian'),
                            ('ZW', 'Zimbabwe', 'Zimbabwean')],
            columns_to_display_in_excerpt=[
                {"name": "Response", "id": "raw_response", "type": "text"},
                {"name": "Topic(s)", "id": "description", "type": "text"},
                {"name": "Country", "id": "canonical_country", "type": "text"},
                {"name": "Region", "id": "Region", "type": "text"},
                {"name": "Gender", "id": "gender", "type": "text"},
                # {'name': 'Professional Title', 'id': 'professional_title', 'type': 'text'},
                {"name": "Age", "id": "age_str", "type": "text"},
            ],
            category_hierarchy={
                "NA": {
                    "EDUCATION": "Learning, competence, education, skills and employability",
                    "ENVIRONMENT": "Environment",
                    "HEALTH": "Good health and optimum nutrition",
                    "MENTALHEALTH": "Connectedness, positive values and contribution to society",
                    "POWER": "Agency and resilience",
                    "SAFETY": "Safety and a supportive environment",
                    "OTHER": "All other requests",
                }
            },
        )

        return config

    elif campaign == Campaigns.midwives_voices:
        config = CampaignConfig(
            countries_list=[('MW', 'Malawi', 'Malawian'),
                            ('CA', 'Canada', 'Canadian'),
                            ('EC', 'Ecuador', 'Ecuadorean'),
                            ('BI', 'Burundi', 'Burundian'),
                            ('ZW', 'Zimbabwe', 'Zimbabwean'),
                            ('IN', 'India', 'Indian'),
                            ('FI', 'Finland', 'Finnish'),
                            ('MA', 'Morocco', 'Moroccan'),
                            ('FR', 'France', 'French'),
                            ('US', 'United States', 'American'),
                            ('GR', 'Greece', 'Greek'),
                            ('FJ', 'Fiji', 'Fijian'),
                            ('BR', 'Brazil', 'Brazilian'),
                            ('GY', 'Guyana', 'Guyanese'),
                            ('HT', 'Haiti', 'Haitian'),
                            ('AG', 'Antigua and Barbuda', 'Antiguan and Barbudan'),
                            ('ZA', 'South Africa', 'South African'),
                            ('NP', 'Nepal', 'Nepalese'),
                            ('ET', 'Ethiopia', 'Ethiopian'),
                            ('PG', 'Papua New Guinea', 'Papua New Guinean'),
                            ('GH', 'Ghana', 'Ghanaian'),
                            ('AR', 'Argentina', 'Argentinean'),
                            ('SE', 'Sweden', 'Swedish'),
                            ('MT', 'Malta', 'Maltese'),
                            ('LS', 'Lesotho', 'Mosotho'),
                            ('NL', 'Netherlands', 'Dutch'),
                            ('LR', 'Liberia', 'Liberian'),
                            ('BB', 'Barbados', 'Barbadian'),
                            ('NZ', 'New Zealand', 'New Zealander'),
                            ('BJ', 'Benin', 'Beninese'),
                            ('LT', 'Lithuania', 'Lithuanian'),
                            ('VG', 'British Virgin Islands', 'British Virgin Islander'),
                            ('KH', 'Cambodia', 'Cambodian'),
                            ('BH', 'Bahrain', 'Bahraini'),
                            ('DK', 'Denmark', 'Danish'),
                            ('AF', 'Afghanistan', 'Afghan'),
                            ('IL', 'Israel', 'Israeli'),
                            ('SA', 'Saudi Arabia', 'Saudi Arabian'),
                            ('BW', 'Botswana', 'Motswana'),
                            ('SY', 'Syria', 'Syrian'),
                            ('ID', 'Indonesia', 'Indonesian'),
                            ('PL', 'Poland', 'Polish'),
                            ('PH', 'Philippines', 'Filipino'),
                            ('ML', 'Mali', 'Malian'),
                            ('RW', 'Rwanda', 'Rwandan'),
                            ('BT', 'Bhutan', 'Bhutanese'),
                            ('UY', 'Uruguay', 'Uruguayan'),
                            ('TG', 'Togo', 'Togolese'),
                            ('AT', 'Austria', 'Austrian'),
                            ('ER', 'Eritrea', 'Eritrean'),
                            ('GT', 'Guatemala', 'Guatemalan'),
                            ('PF', 'French Polynesia', 'French Polynesian'),
                            ('TL', 'Timor-Leste', 'East Timorese'),
                            ('LC', 'Saint Lucia', 'Saint Lucian'),
                            ('CH', 'Switzerland', 'Swiss'),
                            ('AU', 'Australia', 'Australian'),
                            ('NO', 'Norway', 'Norwegian'),
                            ('TZ', 'Tanzania, United Republic of', 'Tanzanian'),
                            ('CM', 'Cameroon', 'Cameroonian'),
                            ('CL', 'Chile', 'Chilean'),
                            ('TR', 'Turkey', 'Turkish'),
                            ('SN', 'Senegal', 'Senegalese'),
                            ('GM', 'Gambia', 'Gambian'),
                            ('BD', 'Bangladesh', 'Bangladeshi'),
                            ('DZ', 'Algeria', 'Algerian'),
                            ('CR', 'Costa Rica', 'Costa Rican'),
                            ('KE', 'Kenya', 'Kenyan'),
                            ('RO', 'Romania', 'Romanian'),
                            ('MX', 'Mexico', 'Mexican'),
                            ('IE', 'Ireland', 'Irish'),
                            ('CI', "Côte d'Ivoire", 'Ivorian'),
                            ('UG', 'Uganda', 'Ugandan'),
                            ('IT', 'Italy', 'Italian'),
                            ('BF', 'Burkina Faso', 'Burkinabe'),
                            ('TT', 'Trinidad and Tobago', 'Trinidadian'),
                            ('DM', 'Dominica', 'Dominican'),
                            ('JM', 'Jamaica', 'Jamaican'),
                            ('SR', 'Suriname', 'Surinamer'),
                            ('KN', 'Saint Kitts and Nevis', 'Kittian and Nevisian'),
                            ('IS', 'Iceland', 'Icelander'),
                            ('PY', 'Paraguay', 'Paraguayan'),
                            ('PK', 'Pakistan', 'Pakistani'),
                            ('ZM', 'Zambia', 'Zambian'),
                            ('BG', 'Bulgaria', 'Bulgarian'),
                            ('PE', 'Peru', 'Peruvian'),
                            ('BS', 'Bahamas', 'Bahamian'),
                            ('SD', 'Sudan', 'Sudanese'),
                            ('GB', 'United Kingdom', 'British'),
                            ('SL', 'Sierra Leone', 'Sierra Leonean'),
                            ('AE', 'United Arab Emirates', 'Emirati'),
                            ('DE', 'Germany', 'German'),
                            ('IR', 'Iran, Islamic Republic of', 'Iranian'),
                            ('NA', 'Namibia', 'Namibian'),
                            ('ES', 'Spain', 'Spanish'),
                            ('VU', 'Vanuatu', 'Ni-Vanuatu'),
                            ('GA', 'Gabon', 'Gabonese'),
                            ('CD', 'The Democratic Republic of the Congo', 'DRC Congolese'),
                            ('SS', 'South Sudan', 'South Sudanese'),
                            ('SO', 'Somalia', 'Somali'),
                            ('NG', 'Nigeria', 'Nigerian'),
                            ('PT', 'Portugal', 'Portuguese')],
            columns_to_display_in_excerpt=[
                {"name": "Response", "id": "raw_response", "type": "text"},
                {"name": "Topic(s)", "id": "description", "type": "text"},
                {"name": "Country", "id": "canonical_country", "type": "text"},
                {"name": "Region", "id": "Region", "type": "text"},
                {"name": "Gender", "id": "gender", "type": "text"},
                {"name": "Professional Title", "id": "professional_title", "type": "text"},
                {"name": "Age", "id": "age_str", "type": "text"},
            ],
            category_hierarchy={
                "NA": {
                    "BETTERFACILITIESANDSUPPLIES": "Supplies and functional facilities",
                    "DIGNITY": "Respect, dignity, and non-discrimination",
                    "POLICY": "Power, autonomy and improved gender norms and policies",
                    "HEALTHANDSERVICES": "General health and health services",
                    "OTHER": "All other requests",
                    "PROFDEV": "Professional development and leadership",
                    "STAFFINGANDREMUNERATION": "More and better supported personnel",
                }
            },
        )

        return config
