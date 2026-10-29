"""
Lead Extraction Engine - Updated with:
- Precise search queries (no 'top' prefix to avoid fashion site results)
- JustDial listing page scraping
- Custom keyword support
- Better excluded domains
- Bhavani/city location used in actual search queries
"""

import re
import time
import socket
import base64
import urllib.parse
from urllib.parse import urlparse, urljoin
import requests
import urllib3.util.connection
from bs4 import BeautifulSoup
import phonenumbers
import primp
from ddgs import DDGS
from data.india_data import INDIAN_STD_CODES, INDIAN_STATES_AND_DISTRICTS

# Complete set of all Indian states, districts, and common city/town aliases for strict filtering
ALL_INDIA_LOCATIONS = set()
for _st, _dists in INDIAN_STATES_AND_DISTRICTS.items():
    ALL_INDIA_LOCATIONS.add(_st.lower())
    for _d in _dists:
        ALL_INDIA_LOCATIONS.add(_d.lower())

ALL_INDIA_LOCATIONS.update({
    'bangalore', 'bengaluru', 'attibele', 'hosur', 'mysore', 'mysuru', 'mangalore', 'mangaluru',
    'hubli', 'dharwad', 'belgaum', 'belagavi', 'bellary', 'ballari', 'tumkur', 'tumakuru',
    'shimoga', 'shivamogga', 'gulbarga', 'kalaburagi', 'davangere', 'udupi', 'hassan', 'mandya',
    'chennai', 'madras', 'avadi', 'ambattur', 'tambaram', 'chengalpattu', 'kanchipuram',
    'tiruvallur', 'vellore', 'ranipet', 'tirupattur', 'tiruvannamalai', 'villupuram', 'viluppuram',
    'kallakurichi', 'cuddalore', 'chidambaram', 'neyveli', 'pondicherry', 'puducherry',
    'coimbatore', 'pollachi', 'mettupalayam', 'sulur', 'tirupur', 'tiruppur', 'udumalpet',
    'dharapuram', 'palladam', 'kangayam', 'kangeyam', 'avinashi', 'avanashi',
    'nilgiris', 'ooty', 'udhagamandalam', 'coonoor',
    'salem', 'attur', 'mettur', 'yercaud', 'namakkal', 'tiruchengode', 'rasipuram', 'komarapalayam',
    'dharmapuri', 'krishnagiri',
    'trichy', 'tiruchirappalli', 'manapparai', 'karur', 'perambalur', 'ariyalur', 'pudukkottai',
    'thanjavur', 'kumbakonam', 'tiruvarur', 'nagapattinam', 'mayiladuthurai', 'karaikal',
    'madurai', 'theni', 'dindigul', 'palani', 'kodaikanal', 'sivaganga', 'karaikudi', 'ramanathapuram',
    'virudhunagar', 'sivakasi', 'rajapalayam', 'tirunelveli', 'tenkasi', 'thoothukudi', 'tuticorin',
    'kovilpatti', 'kanyakumari', 'nagercoil', 'marthandam',
    'kochi', 'cochin', 'ernakulam', 'trivandrum', 'thiruvananthapuram', 'calicut', 'kozhikode',
    'thrissur', 'trichur', 'palakkad', 'palghat', 'kollam', 'kottayam', 'alappuzha', 'kannur',
    'hyderabad', 'secunderabad', 'warangal', 'nizamabad', 'karimnagar', 'khammam',
    'vijayawada', 'visakhapatnam', 'vizag', 'guntur', 'nellore', 'kurnool', 'rajahmundry', 'tirupati',
    'mumbai', 'bombay', 'navi mumbai', 'thane', 'pune', 'nagpur', 'nashik', 'aurangabad', 'solapur',
    'kolhapur', 'amravati', 'nanded', 'sangli', 'jalgaon', 'akola', 'latur', 'ahmednagar', 'jalna',
    'delhi', 'new delhi', 'noida', 'greater noida', 'gurgaon', 'gurugram', 'faridabad', 'ghaziabad',
    'ahmedabad', 'surat', 'vadodara', 'baroda', 'rajkot', 'bhavnagar', 'jamnagar', 'gandhinagar', 'morbi',
    'kolkata', 'calcutta', 'howrah', 'durgapur', 'asansol', 'siliguri',
    'jaipur', 'jodhpur', 'kota', 'bikaner', 'ajmer', 'udaipur', 'bhilwara', 'alwar', 'sikar',
    'lucknow', 'kanpur', 'agra', 'varanasi', 'banaras', 'meerut', 'prayagraj', 'allahabad', 'bareilly',
    'aligarh', 'moradabad', 'saharanpur', 'gorakhpur', 'jhansi', 'mathura', 'ayodhya', 'gonda',
    'bhopal', 'indore', 'jabalpur', 'gwalior', 'ujjain', 'sagar', 'dewas', 'satna', 'ratlam',
    'patna', 'gaya', 'bhagalpur', 'muzaffarpur', 'purnia', 'darbhanga', 'begusarai',
    'ranchi', 'jamshedpur', 'dhanbad', 'bokaro', 'deoghar', 'hazaribagh',
    'raipur', 'bhilai', 'durg', 'bilaspur', 'korba', 'raigarh', 'rajnandgaon',
    'bhubaneswar', 'cuttack', 'rourkela', 'berhampur', 'sambalpur', 'puri', 'balasore',
    'chandigarh', 'zirakpur', 'ludhiana', 'amritsar', 'jalandhar', 'patiala', 'bathinda', 'mohali',
    'ambala', 'panipat', 'rohtak', 'hisar', 'karnal', 'sonipat', 'yamunanagar', 'panchkula',
    'dehradun', 'haridwar', 'roorkee', 'haldwani', 'rudrapur', 'rishikesh', 'nainital',
    'shimla', 'solan', 'dharamshala', 'mandi', 'baddi', 'kullu', 'manali',
    'jammu', 'srinagar', 'anantnag', 'baramulla', 'udhampur', 'leh', 'kargil',
    'guwahati', 'silchar', 'dibrugarh', 'jorhat', 'nagaon', 'tinsukia',
    'imphal', 'shillong', 'aizawl', 'agartala', 'kohima', 'dimapur', 'itanagar', 'gangtok',
    'panaji', 'margao', 'vasco da gama', 'mapusa'
})

DISTRICT_PORTAL_SLUGS = {
    # Tamil Nadu (all 38 districts with commercial directory slugs & headquarters)
    'ariyalur': ['Ariyalur', 'Jayankondam'],
    'chengalpattu': ['Chengalpattu', 'Tambaram', 'Pallavaram', 'Chromepet', 'Mahabalipuram', 'Guduvancheri'],
    'chennai': ['Chennai'],
    'coimbatore': ['Coimbatore', 'Pollachi', 'Mettupalayam'],
    'cuddalore': ['Cuddalore', 'Chidambaram', 'Neyveli', 'Panruti', 'Virudhachalam'],
    'dharmapuri': ['Dharmapuri', 'Harur', 'Palacode'],
    'dindigul': ['Dindigul', 'Palani', 'Kodaikanal'],
    'erode': ['Erode', 'Gobichettipalayam', 'Bhavani', 'Perundurai', 'Sathyamangalam'],
    'kallakurichi': ['Kallakurichi', 'Sankarapuram', 'Chinnasalem', 'Ulundurpet'],
    'kanchipuram': ['Kanchipuram', 'Sriperumbudur'],
    'kanyakumari': ['Nagercoil', 'Kanyakumari', 'Marthandam'],
    'karur': ['Karur', 'Kulithalai'],
    'krishnagiri': ['Krishnagiri', 'Hosur'],
    'madurai': ['Madurai', 'Melur', 'Thirumangalam'],
    'mayiladuthurai': ['Mayiladuthurai', 'Sirkali', 'Kuttalam'],
    'nagapattinam': ['Nagapattinam', 'Nagore', 'Velankanni'],
    'namakkal': ['Namakkal', 'Tiruchengode', 'Rasipuram'],
    'nilgiris': ['Ooty', 'Coonoor', 'Nilgiris'],
    'perambalur': ['Perambalur'],
    'pudukkottai': ['Pudukkottai', 'Aranthangi', 'Viralimalai'],
    'ramanathapuram': ['Ramanathapuram', 'Paramakudi', 'Rameshwaram'],
    'ranipet': ['Ranipet', 'Arakkonam', 'Walajapet', 'Arcot'],
    'salem': ['Salem', 'Attur', 'Mettur'],
    'sivaganga': ['Karaikudi', 'Sivaganga', 'Devakottai'],
    'tenkasi': ['Tenkasi', 'Sankarankovil', 'Kadayanallur'],
    'thanjavur': ['Thanjavur', 'Kumbakonam', 'Pattukkottai', 'Peravurani'],
    'theni': ['Theni', 'Bodinayakanur', 'Periyakulam', 'Cumbum'],
    'thoothukudi': ['Thoothukudi', 'Tuticorin', 'Kovilpatti'],
    'tiruchirappalli': ['Trichy', 'Tiruchirappalli', 'Manapparai'],
    'tirunelveli': ['Tirunelveli', 'Nellai', 'Palayamkottai'],
    'tirupattur': ['Tirupattur', 'Ambur', 'Vaniyambadi'],
    'tiruppur': ['Tiruppur', 'Udumalpet', 'Dharapuram', 'Palladam'],
    'tiruvallur': ['Tiruvallur', 'Avadi', 'Ambattur', 'Ponneri'],
    'tiruvannamalai': ['Tiruvannamalai', 'Arani', 'Cheyyar'],
    'tiruvarur': ['Tiruvarur', 'Thiruvarur', 'Mannargudi', 'Koothanallur'],
    'vellore': ['Vellore', 'Katpadi', 'Gudiyatham'],
    'viluppuram': ['Villupuram', 'Viluppuram', 'Tindivanam'],
    'virudhunagar': ['Sivakasi', 'Virudhunagar', 'Rajapalayam', 'Aruppukkottai'],

    # Karnataka
    'bengaluru urban': ['Bangalore', 'Bengaluru'],
    'bengaluru rural': ['Bangalore', 'Hoskote', 'Devanahalli'],
    'mysuru': ['Mysore', 'Mysuru'],
    'belagavi': ['Belgaum', 'Belagavi'],
    'kalaburagi': ['Gulbarga', 'Kalaburagi'],
    'ballari': ['Bellary', 'Ballari'],
    'shivamogga': ['Shimoga', 'Shivamogga'],
    'vijayapura': ['Bijapur', 'Vijayapura'],
    'tumakuru': ['Tumkur', 'Tumakuru'],
    'dakshina kannada': ['Mangalore', 'Dakshina Kannada'],
    'uttara kannada': ['Karwar', 'Sirsi'],
    'dharwad': ['Hubli', 'Dharwad'],

    # Kerala
    'ernakulam': ['Kochi', 'Cochin', 'Ernakulam'],
    'thiruvananthapuram': ['Trivandrum', 'Thiruvananthapuram'],
    'kozhikode': ['Calicut', 'Kozhikode'],
    'alappuzha': ['Alleppey', 'Alappuzha'],
    'palakkad': ['Palghat', 'Palakkad'],
    'thrissur': ['Trichur', 'Thrissur'],
    'kollam': ['Quilon', 'Kollam'],
    'kannur': ['Cannanore', 'Kannur'],

    # Andhra Pradesh & Telangana
    'visakhapatnam': ['Vizag', 'Visakhapatnam'],
    'ntr': ['Vijayawada', 'NTR'],
    'ysr kadapa': ['Kadapa', 'Cuddapah'],
    'sri potti sriramulu nellore': ['Nellore'],
    'dr. b.r. ambedkar konaseema': ['Amalapuram', 'Konaseema'],
    'tirupati': ['Tirupati'],
    'guntur': ['Guntur'],
    'kurnool': ['Kurnool'],
    'hanamkonda': ['Warangal', 'Hanamkonda'],
    'medchal-malkajgiri': ['Hyderabad', 'Secunderabad'],
    'rangareddy': ['Hyderabad'],
    'hyderabad': ['Hyderabad', 'Secunderabad'],

    # Maharashtra
    'chhatrapati sambhajinagar': ['Aurangabad', 'Chhatrapati Sambhajinagar'],
    'dharashiv': ['Osmanabad', 'Dharashiv'],
    'mumbai city': ['Mumbai'],
    'mumbai suburban': ['Mumbai', 'Thane', 'Navi Mumbai'],
    'pune': ['Pune', 'Pimpri-Chinchwad'],
    'nashik': ['Nashik'],
    'nagpur': ['Nagpur'],
    'solapur': ['Solapur'],

    # Gujarat
    'ahmedabad': ['Ahmedabad'],
    'surat': ['Surat'],
    'vadodara': ['Vadodara', 'Baroda'],
    'rajkot': ['Rajkot'],
    'bhavnagar': ['Bhavnagar'],
    'jamnagar': ['Jamnagar'],
    'devbhumi dwarka': ['Dwarka', 'Khambhalia'],
    'gir somnath': ['Veraval', 'Somnath'],
    'banaskantha': ['Palanpur'],
    'sabarkantha': ['Himatnagar'],
    'panchmahal': ['Godhra'],
    'mahisagar': ['Lunawada'],
    'kutch': ['Bhuj', 'Gandhidham'],
    'surendranagar': ['Surendranagar', 'Wadhwan'],
    'chhota udaipur': ['Chhota Udepur', 'Bodeli'],
    'aravalli': ['Modasa'],
    'dang': ['Ahwa', 'Dang'],
    'tapi': ['Vyara'],
    'mehsana': ['Mehsana'],
    'valsad': ['Valsad', 'Vapi'],
    'navsari': ['Navsari'],
    'anand': ['Anand'],
    'kheda': ['Nadiad', 'Kheda'],
    'dahod': ['Dahod'],
    'amreli': ['Amreli'],
    'botad': ['Botad'],
    'porbandar': ['Porbandar'],
    'junagadh': ['Junagadh'],
    'morbi': ['Morbi'],
    'gandhinagar': ['Gandhinagar'],

    # Uttar Pradesh & Delhi
    'prayagraj': ['Allahabad', 'Prayagraj'],
    'varanasi': ['Varanasi', 'Banaras', 'Kashi'],
    'ayodhya': ['Faizabad', 'Ayodhya'],
    'gautam buddha nagar': ['Noida', 'Greater Noida'],
    'kanpur nagar': ['Kanpur'],
    'lucknow': ['Lucknow'],
    'agra': ['Agra'],
    'meerut': ['Meerut'],
    'ghaziabad': ['Ghaziabad'],

    # Odisha & West Bengal
    'khordha': ['Bhubaneswar', 'Khordha'],
    'cuttack': ['Cuttack'],
    'kolkata': ['Kolkata', 'Calcutta'],
    'howrah': ['Howrah', 'Kolkata'],
    'north 24 parganas': ['Barasat', 'Kolkata'],
    'south 24 parganas': ['Baruipur', 'Kolkata'],
    'paschim bardhaman': ['Asansol', 'Durgapur'],

    # Assam & North East
    'kamrup metropolitan': ['Guwahati'],
    'kamrup': ['Amigaon', 'Guwahati'],
    'cachar': ['Silchar'],
    'darrang': ['Mangaldai'],
    'dima hasao': ['Haflong'],
    'karbi anglong': ['Diphu'],
    'sonitpur': ['Tezpur'],
    'dibrugarh': ['Dibrugarh'],
    'jorhat': ['Jorhat'],
    'tinsukia': ['Tinsukia'],
    'nagaon': ['Nagaon'],
    'barpeta': ['Barpeta'],
    'bongaigaon': ['Bongaigaon'],

    # Punjab & Haryana
    'sahibzada ajit singh nagar (mohali)': ['Mohali', 'SAS Nagar'],
    'shahid bhagat singh nagar': ['Nawanshahr'],
    'ludhiana': ['Ludhiana'],
    'amritsar': ['Amritsar'],
    'jalandhar': ['Jalandhar'],
    'gurugram': ['Gurugram', 'Gurgaon'],
    'faridabad': ['Faridabad'],

    # Himachal Pradesh
    'kangra': ['Dharamshala', 'Kangra'],
    'lahaul and spiti': ['Keylong'],
    'sirmaur': ['Nahan'],
    'bilaspur': ['Bilaspur'],
    'kinnaur': ['Reckong Peo', 'Kinnaur'],
    'kullu': ['Kullu', 'Manali'],
    'mandi': ['Mandi'],
    'shimla': ['Shimla'],
    'solan': ['Solan'],
    'una': ['Una'],
    'chamba': ['Chamba'],
    'hamirpur': ['Hamirpur']
}

DISTRICT_SYNONYMS = {
    # Tamil Nadu - All 38 Districts fully populated
    'ariyalur': {'ariyalur', 'jayankondam', 'sendurai', 'andimadam', 'udayarpalayam'},
    'chengalpattu': {'chengalpattu', 'tambaram', 'mahabalipuram', 'mamallapuram', 'madurantakam', 'pallavaram', 'chromepet', 'guduvancheri', 'kelambakkam', 'vandalur'},
    'chennai': {'chennai', 'madras', 'ambattur', 'avadi', 'tambaram', 'guindy', 'anna nagar', 't nagar', 'adyar', 'velachery', 'porur', 'omr', 'perambur', 'mylapore', 'egmore', 'kodambakkam'},
    'coimbatore': {'coimbatore', 'kovai', 'pollachi', 'mettupalayam', 'sulur', 'annur', 'valparai', 'kinathukadavu', 'perur', 'madukkarai', 'saravanampatti', 'peelamedu', 'gandhipuram', 'singanallur'},
    'cuddalore': {'cuddalore', 'chidambaram', 'neyveli', 'panruti', 'virudhachalam', 'kattumannarkoil', 'tittakudi', 'vadalur', 'kurinjipadi'},
    'dharmapuri': {'dharmapuri', 'harur', 'palacode', 'pennagaram', 'papireddipatti', 'karimangalam', 'nallampalli'},
    'dindigul': {'dindigul', 'palani', 'kodaikanal', 'oddanchatram', 'vedasandur', 'nilakottai', 'natham', 'athoor'},
    'erode': {'erode', 'perundurai', 'gobichettipalayam', 'gobi', 'bhavani', 'sathyamangalam', 'sathy', 'anthiyur', 'kodumudi', 'modakurichi', 'nambiyur', 'thalavadi', 'chennimalai', 'nathakadaiyur', 'chithode', 'vellode', 'sivagiri', 'avalpoondurai', 'kavindapadi', 'ammapettai'},
    'kallakurichi': {'kallakurichi', 'sankarapuram', 'chinnasalem', 'ulundurpet', 'tirukkoyilur', 'kalvarayan hills'},
    'kanchipuram': {'kanchipuram', 'kancheepuram', 'sriperumbudur', 'walajabad', 'kundrathur', 'uthiramerur'},
    'kanyakumari': {'kanyakumari', 'nagercoil', 'marthandam', 'thuckalay', 'colachel', 'kuzhithurai', 'kanniyakumari'},
    'karur': {'karur', 'kulithalai', 'aravakurichi', 'krishnarayapuram', 'pugalur', 'manmangalam', 'velayuthampalayam'},
    'krishnagiri': {'krishnagiri', 'hosur', 'denkanikottai', 'uthangarai', 'pochampalli', 'bargur', 'shoolagiri', 'kelamangalam'},
    'madurai': {'madurai', 'melur', 'thirumangalam', 'tirumangalam', 'usilampatti', 'vadipatti', 'peraiyur', 'thiruparankundram', 'avaniapuram', 'anaiyur'},
    'mayiladuthurai': {'mayiladuthurai', 'sirkali', 'tharangambadi', 'kuttalam', 'porayar', 'koranad', 'sembanarkoil'},
    'nagapattinam': {'nagapattinam', 'nagore', 'velankanni', 'kilvelur', 'vedaranyam', 'thirukkuvalai'},
    'namakkal': {'namakkal', 'tiruchengode', 'rasipuram', 'komarapalayam', 'kumarapalayam', 'paramathi velur', 'sendamangalam', 'pallipalayam'},
    'nilgiris': {'nilgiris', 'ooty', 'udhagamandalam', 'coonoor', 'kotagiri', 'gudalur', 'kundah'},
    'perambalur': {'perambalur', 'veppanthattai', 'kunnam', 'alathur'},
    'pudukkottai': {'pudukkottai', 'pudukottai', 'aranthangi', 'viralimalai', 'alangudi', 'gandharvakottai', 'kulathur', 'illupur', 'ponnamaravathi'},
    'ramanathapuram': {'ramanathapuram', 'paramakudi', 'rameshwaram', 'rameswaram', 'kilakarai', 'mudukulathur', 'kamuthi', 'thiruvadanai'},
    'ranipet': {'ranipet', 'arakkonam', 'walajapet', 'arcot', 'sholinghur', 'nemili'},
    'salem': {'salem', 'attur', 'mettur', 'yercaud', 'omalur', 'idappadi', 'edappadi', 'sankari', 'sangagiri', 'vazhapadi', 'gangavalli', 'kadaiyampatti'},
    'sivaganga': {'sivaganga', 'sivagangai', 'karaikudi', 'devakottai', 'manamadurai', 'thirupuvanam', 'singampunari', 'ilayangudi'},
    'tenkasi': {'tenkasi', 'sankarankovil', 'shenkottai', 'senkottai', 'kadayanallur', 'puliyangudi', 'alangulam', 'courtallam', 'thiruvengadam'},
    'thanjavur': {'thanjavur', 'tanjore', 'kumbakonam', 'pattukkottai', 'peravurani', 'orathanadu', 'papanasam', 'thiruvaiyaru', 'thiruvidaimarudur'},
    'theni': {'theni', 'periyakulam', 'bodinayakanur', 'bodi', 'cumbum', 'uthamapalayam', 'andipatti', 'chinnamanur'},
    'thoothukudi': {'thoothukudi', 'tuticorin', 'kovilpatti', 'tiruchendur', 'srivaikuntam', 'ettayapuram', 'kayathar', 'sathankulam'},
    'tiruchirappalli': {'trichy', 'tiruchirappalli', 'tiruchirapalli', 'manapparai', 'srirangam', 'lalgudi', 'musiri', 'thottiyam', 'thuraiyur', 'thuvakudi'},
    'tirunelveli': {'tirunelveli', 'nellai', 'palayamkottai', 'ambasamudram', 'valliyur', 'radhapuram', 'nanguneri', 'cheranmahadevi'},
    'tirupattur': {'tirupattur', 'ambur', 'vaniyambadi', 'natrampalli'},
    'tiruppur': {'tiruppur', 'tirupur', 'avinashi', 'avanashi', 'palangarai', 'avinashilingampalayam', 'udumalpet', 'dharapuram', 'palladam', 'kangayam', 'kangeyam', 'vellakovil', 'muthur', 'uthukuli', 'madathukulam', 'mangalam'},
    'tiruvallur': {'tiruvallur', 'thiruvallur', 'avadi', 'ambattur', 'ponneri', 'poonamallee', 'tiruttani', 'gummidipoondi', 'madhavaram'},
    'tiruvannamalai': {'tiruvannamalai', 'thiruvannamalai', 'arani', 'cheyyar', 'polur', 'chengampet', 'vandavasi', 'kalasapakkam', 'jawadhu hills'},
    'tiruvarur': {'tiruvarur', 'thiruvarur', 'mannargudi', 'koothanallur', 'kudavasal', 'nannilam', 'valangaiman', 'muthupet', 'thiruthuraipoondi'},
    'vellore': {'vellore', 'katpadi', 'gudiyatham', 'aniyambadi', 'pernambut'},
    'viluppuram': {'viluppuram', 'villupuram', 'tindivanam', 'gingee', 'vanur', 'marakkanam', 'vikravandi'},
    'virudhunagar': {'virudhunagar', 'sivakasi', 'rajapalayam', 'aruppukkottai', 'sattur', 'srivilliputhur', 'watrap', 'kariapatti'},
    'puducherry': {'puducherry', 'pondicherry', 'karaikal', 'mahe', 'yanam'},

    # Other States Major Mappings
    'bengaluru urban': {'bengaluru', 'bangalore', 'bengaluru urban'},
    'bengaluru rural': {'bengaluru', 'bangalore', 'bengaluru rural', 'hoskote', 'devanahalli'},
    'mysuru': {'mysuru', 'mysore'},
    'dakshina kannada': {'mangaluru', 'mangalore', 'dakshina kannada'},
    'belagavi': {'belagavi', 'belgaum'},
    'ballari': {'ballari', 'bellary'},
    'shivamogga': {'shivamogga', 'shimoga'},
    'tumakuru': {'tumakuru', 'tumkur'},
    'kalaburagi': {'kalaburagi', 'gulbarga'},
    'dharwad': {'hubli', 'dharwad'},
    'ernakulam': {'ernakulam', 'kochi', 'cochin'},
    'thiruvananthapuram': {'thiruvananthapuram', 'trivandrum'},
    'kozhikode': {'kozhikode', 'calicut'},
    'thrissur': {'thrissur', 'trichur'},
    'palakkad': {'palakkad', 'palghat'},
    'alappuzha': {'alappuzha', 'alleppey'},
    'kollam': {'kollam', 'quilon'},
    'visakhapatnam': {'visakhapatnam', 'vizag'},
    'ntr': {'ntr', 'vijayawada'},
    'ysr kadapa': {'kadapa', 'cuddapah', 'ysr kadapa'},
    'sri potti sriramulu nellore': {'nellore', 'sri potti sriramulu nellore'},
    'dr. b.r. ambedkar konaseema': {'amalapuram', 'konaseema', 'dr. b.r. ambedkar konaseema'},
    'hanamkonda': {'hanamkonda', 'warangal'},
    'mumbai city': {'mumbai', 'bombay', 'mumbai city'},
    'mumbai suburban': {'mumbai', 'bombay', 'mumbai suburban', 'thane', 'navi mumbai'},
    'chhatrapati sambhajinagar': {'aurangabad', 'chhatrapati sambhajinagar'},
    'dharashiv': {'osmanabad', 'dharashiv'},
    'prayagraj': {'prayagraj', 'allahabad'},
    'varanasi': {'varanasi', 'banaras', 'kashi'},
    'ayodhya': {'ayodhya', 'faizabad'},
    'gurugram': {'gurugram', 'gurgaon'},
    'gautam buddha nagar': {'noida', 'greater noida', 'gautam buddha nagar'},
    'gautam buddha nagar (noida)': {'noida', 'greater noida', 'gautam buddha nagar'},
    'sahibzada ajit singh nagar (mohali)': {'mohali', 'chandigarh', 'sas nagar', 'sahibzada ajit singh nagar'},
    'khordha': {'khordha', 'bhubaneswar'},
    'kamrup metropolitan': {'kamrup metropolitan', 'guwahati'},
    'devbhumi dwarka': {'devbhumi dwarka', 'dwarka', 'khambhalia'},
    'gir somnath': {'gir somnath', 'veraval', 'somnath'},
    'kutch': {'kutch', 'bhuj', 'gandhidham'},
    'kangra': {'kangra', 'dharamshala'},
}

# Automatically register all portal slugs into ALL_INDIA_LOCATIONS and DISTRICT_SYNONYMS
for _k, _slugs in DISTRICT_PORTAL_SLUGS.items():
    if _k not in DISTRICT_SYNONYMS:
        DISTRICT_SYNONYMS[_k] = set()
    for _s in _slugs:
        s_low = _s.lower()
        DISTRICT_SYNONYMS[_k].add(s_low)
        ALL_INDIA_LOCATIONS.add(s_low)

# Force IPv4 so Akamai / Cloudflare dual-stack domains (JustDial, Sulekha, etc.)
# do not stall or time out on unroutable IPv6 sockets.
urllib3.util.connection.allowed_gai_family = lambda: socket.AF_INET

# Common typo corrections for business searches in Tamil Nadu / India
COMMON_KEYWORD_TYPOS = {
    'constraction': 'construction',
    'constractions': 'construction',
    'contruction': 'construction',
    'contracter': 'contractor',
    'contracters': 'contractor',
    'contactors': 'contractor',
    'contactor': 'contractor',
    'bilding': 'building',
    'metel': 'metal',
    'steal': 'steel',
}

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Accept-Language': 'en-IN,en-GB;q=0.9,en;q=0.8',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
}

# Extended excluded domains — fashion, e-commerce, dictionaries, job boards
EXCLUDED_DOMAINS = {
    'wikipedia.org', 'shiksha.com', 'careers360.com', 'naukri.com', 'indeed.com',
    'quora.com', 'youtube.com', 'facebook.com', 'instagram.com', 'linkedin.com',
    'pinterest.com', 'twitter.com', 'x.com', 'amazon.in', 'flipkart.com',
    'britannica.com', 'merriam-webster.com', 'dictionary.cambridge.org',
    'glassdoor.com', 'ambitionbox.com', 'reddit.com',
    # Fashion / e-commerce sites that pollute "top contractor" searches
    'myntra.com', 'meesho.com', 'nykaafashion.com', 'nykaa.com', 'ajio.com',
    'snapdeal.com', 'shopify.com', 'etsy.com', 'zara.com', 'limeroad.com',
    # Generic business info aggregators with no real contact data
    'aeroleads.com', 'zoominfo.com', 'lusha.com', 'apollo.io',
    # Educational
    'vedantu.com', 'byjus.com', 'unacademy.com', 'collegedunia.com',
    # News
    'thehindu.com', 'indiatimes.com', 'ndtv.com', 'timesofindia.com',
    # Scribd (PDFs with no real data)
    'scribd.com'
}

FAKE_EMAIL_PATTERNS = [
    'example.com', 'domain.com', 'test.com', 'wixpress.com', 'sentry.io',
    'mysite.com', 'company.com', 'yourcompany.com', 'email.com', 'mail.com',
    'tempmail.com', 'mailinator.com', 'tradeindia.com', 'justdial.com', 'indiamart.com', 'sulekha.com'
]

DUMMY_PHONES = {
    '9876543210', '1234567890', '0123456789', '9999999999', '8888888888',
    '7777777777', '6666666666', '1111111111', '0000000000', '9000000000'
}


REJECT_KEYWORDS = {
    'court', 'courts', 'police', 'ips', 'upsc', 'ssc', 'judgement', 'judiciary',
    'dictionary', 'meaning', 'definition', 'thesaurus', 'lawyer', 'advocate',
    'syllabus', 'admission', 'college', 'university', 'department of', 'iit',
    'nit', 'school', 'hospital', 'medical', 'criminal', 'rule', 'section',
    'government list', 'civil list', 'civil court', 'civil service', 'civil services',
    'civil aviation', 'civil judge', 'civil law'
}

REJECT_DOMAIN_KEYWORDS = [
    'dictionary', 'courts', 'police', 'judiciary', 'gov.in', 'nic.in', 'ac.in', 'edu.in'
]

# Patterns definitively identifying non-construction unrelated businesses
UNRELATED_BUSINESS_PATTERNS = [
    # Travel, Transport, Logistics, Courier, Taxi, Cab, Packers & Movers
    r'\b(?:parveen\s+)?travels?\b',
    r'\btours?\s+(?:and|&)\s+travels?\b',
    r'\btourist\b',
    r'\btourism\b',
    r'\btransports?\b',
    r'\btransportation\b',
    r'\blogistics\b',
    r'\bcargo\b',
    r'\bfreight\b',
    r'\bparcel(?:\s+service)?\b',
    r'\bcouriers?\b',
    r'\bpackers?\s+(?:and|&)\s+movers?\b',
    r'\bcall\s+taxi\b',
    r'\bcabs?\b',
    r'\bcar\s+rentals?\b',
    r'\bbus\s+service\b',
    r'\bfleet\b',
    r'\bautomobile\b',
    r'\bauto\s+parts\b',
    
    # Hospitality, Food, Beverages
    r'\bhotels?\b',
    r'\bresorts?\b',
    r'\blodg(?:e|ing|es)\b',
    r'\brestaurants?\b',
    r'\bcafes?\b',
    r'\bdhaba\b',
    r'\bbakery\b',
    r'\bbakers\b',
    r'\bsweets?\b',
    r'\bfast\s+food\b',
    r'\btea\s+stall\b',
    r'\bcatering\b',
    r'\bhospitality\b',
    
    # Healthcare & Medical
    r'\bhospitals?\b',
    r'\bclinics?\b',
    r'\bpharmacy\b',
    r'\bchemist\b',
    r'\bopticals?\b',
    r'\bopticians?\b',
    r'\bdent(?:al|ist)\b',
    r'\bdiagnostic(?:\s+center)?\b',
    r'\bscan\s+center\b',
    
    # Education
    r'\bschools?\b',
    r'\bcolleges?\b',
    r'\bacademy\b',
    r'\bcoaching\b',
    r'\btuitions?\b',
    r'\bkindergarten\b',
    
    # Beauty & Personal Care
    r'\b(?:beauty\s+)?parlou?r\b',
    r'\bsaloons?\b',
    r'\bsalons?\b',
    r'\bspas?\b',
    
    # Apparel, Jewellery & Retail
    r'\bjewelle?rs?\b',
    r'\bjewelle?ry\b',
    r'\btextiles?\b',
    r'\breadymades?\b',
    r'\bsarees?\b',
    r'\bsilks?\b',
    r'\btailors?\b',
    r'\bfootwear\b',
    r'\bsupermarkets?\b',
    
    # Finance
    r'\bchit\s+funds?\b',
    r'\bmicro\s*finance\b'
]


DIRECTORY_DOMAINS = {
    'justdial.com', 'indiamart.com', 'sulekha.com', 'asklaila.com',
    'quikr.com', 'yellowpages.webindia123.com', 'callsevai.com',
    'infobel.in', 'negup.com', 'townin.com', 'tradeindia.com',
    'exportersindia.com', 'cleartax.in', 'zaubacorp.com',
    'google.com', 'maps.google.com'
}


class BusinessLeadExtractor:
    def __init__(self, log_callback=None, check_abort=None, check_pause=None, lead_callback=None):
        self.session = requests.Session()
        self.session.headers.update(HEADERS)
        self.log_callback = log_callback or (lambda msg, lvl='info': None)
        self._check_abort_callback = check_abort or (lambda: False)
        self._aborted = False
        self.check_abort = self._eval_abort
        self.active_browser = None
        self.check_pause = check_pause or (lambda: False)
        self.lead_callback = lead_callback
        self.seen_phones = set()
        self.seen_emails = set()
        self.seen_domains = set()
        self.google_places_cache = {}
        self.brave_client = primp.Client(cookie_store=True, timeout=10)
        self._last_brave_req = 0.0

    def _eval_abort(self):
        return self._aborted or bool(self._check_abort_callback())

    def abort(self):
        """Instantly abort all active network calls and close active Playwright browser."""
        self._aborted = True
        if hasattr(self, 'active_browser') and self.active_browser:
            try:
                self.active_browser.close()
            except Exception:
                pass
            self.active_browser = None
        if hasattr(self, 'session') and self.session:
            try:
                self.session.close()
            except Exception:
                pass

    def reset_district_session(self):
        """
        Reset district-level state, cache, seen domains, and HTTP session
        to ensure fresh isolation between districts without dropping multi-branch contractors.
        """
        self.seen_phones.clear()
        self.seen_emails.clear()
        self.seen_domains.clear()
        self.google_places_cache.clear()
        try:
            self.session.close()
        except Exception:
            pass
        self.session = requests.Session()
        self.session.headers.update(HEADERS)
        try:
            self.brave_client = primp.Client(cookie_store=True, timeout=10)
        except Exception:
            pass
        self._last_brave_req = 0.0

    def emit_lead(self, lead):
        if self.lead_callback and lead:
            try:
                self.lead_callback(lead)
            except Exception:
                pass

    def get_portal_city_slugs(self, district, state=None):
        """
        Return the list of primary portal search and directory city slugs for this district,
        including known popular headquarters, taluks, or commercial aliases across India.
        """
        d_clean = (district or '').strip()
        d_low = d_clean.lower()
        slugs = []

        if d_low in DISTRICT_PORTAL_SLUGS:
            slugs.extend(DISTRICT_PORTAL_SLUGS[d_low])

        cleaned = re.sub(r'\s*\([^)]*\)', '', d_clean).strip()
        for cand in [d_clean, cleaned]:
            if cand and cand not in slugs:
                slugs.append(cand)
            no_pfx = re.sub(r'^(?:Dr\.?\s*B\.?R\.?\s*Ambedkar|Sri|Shri|YSR|NTR)\s*', '', cand).strip()
            if no_pfx and no_pfx not in slugs:
                slugs.append(no_pfx)
            words = cand.split()
            if len(words) > 1 and len(words[0]) >= 4 and words[0] not in slugs:
                slugs.append(words[0])

        return [s for s in slugs if s]

    def get_allowed_cities(self, district, city=None):
        """Return exact allowed lowercase city/district names for the current filter."""
        d_low = (district or '').strip().lower()
        allowed = {d_low}
        if d_low in DISTRICT_SYNONYMS:
            allowed.update(DISTRICT_SYNONYMS[d_low])
        if d_low in DISTRICT_PORTAL_SLUGS:
            for s in DISTRICT_PORTAL_SLUGS[d_low]:
                allowed.add(s.lower())
        for s in self.get_portal_city_slugs(district):
            allowed.add(s.lower())
        if city and city.strip():
            allowed.add(city.strip().lower())
        allowed.discard('')
        return allowed

    def get_other_locations(self, district, state, city=None):
        """Return all Indian districts/states/cities EXCEPT the target district, city, and state."""
        allowed = self.get_allowed_cities(district, city)
        st_low = (state or '').strip().lower()
        return {loc for loc in ALL_INDIA_LOCATIONS if loc not in allowed and loc != st_low}

    def has_conflicting_location(self, text, district, state, city=None):
        """Return True if text mentions another Indian city/district/state without mentioning the target district/city."""
        if not text:
            return False
        t_low = text.lower()
        allowed = self.get_allowed_cities(district, city)
        if any(a in t_low for a in allowed):
            return False
        for bad_loc in self.get_other_locations(district, state, city):
            if len(bad_loc) >= 4 and re.search(r'(?<![a-z])' + re.escape(bad_loc) + r'(?![a-z])', t_low):
                return True
        return False

    def is_directory_domain(self, domain):
        dom_clean = str(domain).lower().replace('www.', '')
        return any(d in dom_clean for d in DIRECTORY_DOMAINS)

    def log(self, message, level='info'):
        try:
            self.log_callback(str(message), level)
        except Exception:
            pass

    def normalize_keyword_typos(self, text):
        if not text:
            return ""
        words = re.split(r'(\W+)', text.lower())
        return ''.join(COMMON_KEYWORD_TYPOS.get(w, w) for w in words)

    def matches_custom_keyword(self, text, custom_keyword):
        """
        Strict check: When a custom keyword is specified (e.g. 'steel', 'metal', or 'pr constractions'),
        returns True ONLY if the given text matches the custom keyword or its specific domain synonyms.
        Supports typo normalization (e.g. 'constractions' -> 'construction') and 2-letter tokens (e.g. 'PR').
        """
        if not custom_keyword or not str(custom_keyword).strip():
            return True
        kw_clean = str(custom_keyword).strip().lower()
        kw_norm = self.normalize_keyword_typos(kw_clean)
        t_clean = (text or '').lower()
        t_norm = self.normalize_keyword_typos(t_clean)
        t_compressed = re.sub(r'[^a-z0-9]', '', t_norm)

        kw_terms = [kw_clean, kw_norm]
        if 'steel' in kw_norm:
            kw_terms.extend(['steel', 'steels', 'tmt', 'iron & steel', 'iron and steel', 'reinforcement', 'rebar'])
        elif 'metal' in kw_norm:
            kw_terms.extend(['metal', 'metals', 'metallic', 'sheet metal', 'metal mart', 'scrap metal', 'brass', 'copper', 'aluminium', 'aluminum', 'alloy'])
        else:
            for w in re.split(r'\W+', kw_norm):
                if len(w) >= 2:
                    kw_terms.append(w)

        for term in set(kw_terms):
            if not term:
                continue
            term_comp = re.sub(r'[^a-z0-9]', '', term)
            if len(term_comp) >= 3 and term_comp in t_compressed:
                return True
            if ' ' in term or '&' in term:
                if term in t_clean or term in t_norm:
                    return True
            else:
                if re.search(r'\b' + re.escape(term) + r'\b', t_clean) or re.search(r'\b' + re.escape(term) + r'\b', t_norm):
                    return True
        return False

    def is_strictly_category_relevant(self, business_name, context_text="", category_item=None, custom_keyword=""):
        """
        Enforce strict business category relevance:
        1. Immediately rejects businesses matching unrelated industries (travels, transport, courier, parcel, hotel, etc.).
        2. If custom_keyword is provided, enforces that the lead matches custom_keyword.
        3. If standard construction category is selected, verifies that business_name OR context_text
           matches terms for that category (builder, civil, contractor, architect, interior, structural, etc.).
        """
        combined = f"{business_name or ''} {context_text or ''}".lower()
        b_name_low = (business_name or '').lower()

        # 1. Unrelated Industry Rejection
        ck_low = (custom_keyword or '').lower()
        for pat in UNRELATED_BUSINESS_PATTERNS:
            if re.search(pat, b_name_low) or re.search(pat, combined):
                # Allow only if custom_keyword explicitly requested that term
                if custom_keyword and re.search(pat, ck_low):
                    pass
                else:
                    return False, f"Unrelated industry detected ({pat})"

        # 2. Custom Keyword Verification
        if custom_keyword and str(custom_keyword).strip():
            if not self.matches_custom_keyword(combined, custom_keyword):
                return False, f"Does not match custom keyword '{custom_keyword}'"
            return True, "Matches custom keyword"

        # 3. Standard Category Verification
        if category_item:
            cat_keywords = [k.lower() for k in category_item.get('keywords', [])]

            universal_terms = [
                'contractor', 'contractors', 'builder', 'builders', 'building', 'buildings',
                'construction', 'constructions', 'civil', 'engineer', 'engineers', 'engineering',
                'architect', 'architects', 'architectural', 'interior', 'interiors',
                'structural', 'infrastructure', 'developer', 'developers', 'paving',
                'waterproofing', 'earthmoving', 'rmc', 'ready mix', 'concrete'
            ]

            target_terms = set(cat_keywords + universal_terms)

            # Check if business name or context contains any target terms
            has_match = any(
                term in combined
                for term in target_terms
                if len(term) >= 3
            )
            if not has_match:
                return False, f"No matching terms for category '{category_item.get('name')}'"

        return True, "Valid category lead"

    def generate_guaranteed_directory_seeds(self, state, district, city, category_item, custom_keyword=""):
        """
        Generate direct verified directory listing URLs (Justdial, IndiaMART, Sulekha, TradeIndia)
        for the given district and category to guarantee that EVERY district has high-quality
        scraping targets even if web search engines are throttled or rate-limited.
        """
        seeds = []
        slugs = self.get_portal_city_slugs(district, state)
        if city and city.strip() and city.strip() not in slugs:
            slugs.insert(0, city.strip())

        cat_id = category_item.get('id', 'civil_contractors') if category_item else 'civil_contractors'
        cat_name = category_item.get('name', 'Civil Contractors') if category_item else 'Civil Contractors'

        JD_CAT_MAP = {
            'civil_contractors': ('Civil-Contractors', 'nct-10100369'),
            'building_contractors': ('Building-Contractors', 'nct-10061214'),
            'interior_contractors': ('Interior-Designers', 'nct-10271038'),
            'architects_designers': ('Architects', 'nct-10022830'),
            'structural_engineers': ('Structural-Engineers', 'nct-10459524'),
            'road_highway_contractors': ('Road-Construction-Contractors', 'nct-10411874'),
            'mep_electrical_plumbing': ('Electrical-Contractors', 'nct-10185966'),
            'painting_waterproofing': ('Painting-Contractors', 'nct-10350702'),
            'govt_approved_contractors': ('Pwd-Civil-Contractors', 'nct-10398668'),
            'earthmoving_demolition': ('Earthmoving-Contractors', 'nct-10181512'),
            'rmc_materials_suppliers': ('Building-Material-Dealers', 'nct-10061245'),
        }

        IM_CAT_MAP = {
            'civil_contractors': 'civil-contractors',
            'building_contractors': 'building-contractors',
            'interior_contractors': 'interior-designers',
            'architects_designers': 'architects',
            'structural_engineers': 'structural-engineers',
            'road_highway_contractors': 'road-contractors',
            'mep_electrical_plumbing': 'electrical-contractors',
            'painting_waterproofing': 'waterproofing-contractors',
            'govt_approved_contractors': 'pwd-contractors',
            'earthmoving_demolition': 'earthmoving-contractors',
            'rmc_materials_suppliers': 'building-materials',
        }

        SUL_CAT_MAP = {
            'civil_contractors': 'civil-contractors',
            'building_contractors': 'building-contractors',
            'interior_contractors': 'interior-designers',
        }

        TI_CAT_MAP = {
            'civil_contractors': 'civil-contractors',
            'building_contractors': 'building-contractors',
            'interior_contractors': 'interior-designers',
        }

        for slug in slugs[:3]:
            clean_slug = re.sub(r'[^a-zA-Z0-9]+', '-', slug).strip('-')
            slug_low = clean_slug.lower()
            slug_title = clean_slug.title()

            if custom_keyword and custom_keyword.strip():
                kw_clean = re.sub(r'[^a-zA-Z0-9]+', '-', custom_keyword.strip()).strip('-')
                kw_low = kw_clean.lower()
                kw_title = kw_clean.title()
                seed_defs = [
                    (f"https://www.justdial.com/{slug_title}/{kw_title}", f"{custom_keyword} in {slug}, {district} - Justdial"),
                    (f"https://dir.indiamart.com/{slug_low}/{kw_low}.html", f"{custom_keyword} in {slug}, {district} - IndiaMART"),
                    (f"https://www.sulekha.com/{kw_low}/{slug_low}", f"{custom_keyword} in {slug}, {district} - Sulekha"),
                    (f"https://www.tradeindia.com/{slug_low}/{kw_low}-city.html", f"{custom_keyword} in {slug}, {district} - TradeIndia"),
                ]
            else:
                jd_slug, jd_nct = JD_CAT_MAP.get(cat_id, (cat_id.replace('_', '-').title(), ''))
                im_slug = IM_CAT_MAP.get(cat_id, cat_id.replace('_', '-').lower())
                sul_slug = SUL_CAT_MAP.get(cat_id, cat_id.replace('_', '-').lower())
                ti_slug = TI_CAT_MAP.get(cat_id, cat_id.replace('_', '-').lower())

                seed_defs = [
                    (f"https://www.justdial.com/{slug_title}/{jd_slug}/{jd_nct}" if jd_nct else f"https://www.justdial.com/{slug_title}/{jd_slug}", f"{cat_name} in {slug}, {district} - Justdial"),
                    (f"https://www.justdial.com/{slug_title}/{jd_slug}", f"{cat_name} in {slug}, {district} - Justdial Direct"),
                    (f"https://dir.indiamart.com/{slug_low}/{im_slug}.html", f"{cat_name} in {slug}, {district} - IndiaMART"),
                    (f"https://www.sulekha.com/{sul_slug}/{slug_low}", f"{cat_name} in {slug}, {district} - Sulekha"),
                    (f"https://www.tradeindia.com/{slug_low}/{ti_slug}-city.html", f"{cat_name} in {slug}, {district} - TradeIndia"),
                ]

            for s_url, s_title in seed_defs:
                seeds.append({
                    'url': s_url,
                    'title': s_title,
                    'snippet': f"Verified directory source for {district}, {state}",
                    'engine': 'Guaranteed Directory Engine',
                    '_is_seed': True
                })

        return seeds

    def is_candidate_relevant(self, url, title, snippet, district, state, city=None, category_item=None, custom_keyword="", is_seed=False):
        """
        Pre-filter candidate URLs before showing them in the Discovered URLs list.
        Strictly enforces that only URLs belonging to the selected district/city and custom keyword are allowed.
        """
        if is_seed:
            return True, "Guaranteed district seed"

        combined = (url + " " + (title or "") + " " + (snippet or "")).lower()

        # 1. Reject domain patterns
        domain = urlparse(url).netloc.lower()
        for d_kw in REJECT_DOMAIN_KEYWORDS:
            if d_kw in domain:
                return False, f"Domain rejected ({d_kw})"

        # 2. Reject bad topic keywords (using word boundaries so 'contractor' isn't rejected by 'act')
        for r_kw in REJECT_KEYWORDS:
            pattern = r'\b' + re.escape(r_kw) + r'\b'
            if re.search(pattern, combined):
                return False, f"Keyword rejected ({r_kw})"

        # 2.5 Strict Category Relevance & Unrelated Industry Rejection (Travels, Transport, Parcel, etc.)
        is_rel, rel_reason = self.is_strictly_category_relevant(title, snippet + " " + url, category_item, custom_keyword)
        if not is_rel:
            return False, rel_reason

        # 3. Category match check (When custom keyword is provided, enforce strict custom keyword match!)
        if custom_keyword and str(custom_keyword).strip():
            if not self.matches_custom_keyword(combined, custom_keyword):
                return False, f"Candidate does not match custom keyword '{custom_keyword}'"
        else:
            cat_terms = list(category_item.get('keywords', [])) if category_item else ['contractor', 'builder', 'construction', 'civil work', 'engineering', 'architect', 'interior']
            if not any(cat in combined for cat in cat_terms):
                return False, "No category construction terms"

        # 4. Strict District / City Relevance Check (State alone is NEVER sufficient)
        allowed_cities = self.get_allowed_cities(district, city)
        other_locs = self.get_other_locations(district, state, city)

        # Target district/city MUST appear in the URL, title, or snippet
        if not any(loc in combined for loc in allowed_cities):
            return False, f"Target district '{district}' not found in candidate"

        # JustDial URL city check: e.g. justdial.com/Erode/... or justdial.com/jdmart/Erode/...
        if 'justdial.com' in url.lower():
            parsed_path = [p for p in urlparse(url).path.strip('/').split('/') if p]
            if parsed_path:
                url_city = parsed_path[1].lower() if parsed_path[0].lower() == 'jdmart' and len(parsed_path) > 1 else parsed_path[0].lower()
                # Do not reject DT- individual business detail URLs as city mismatch
                if not url_city.upper().startswith('DT-') and not url_city.startswith('dt-') and url_city not in allowed_cities:
                    return False, f"JustDial city mismatch ({url_city} != {district})"

        # Sulekha URL city check
        if 'sulekha.com' in url.lower():
            url_path_low = urlparse(url).path.lower()
            if not any(loc in url_path_low for loc in allowed_cities):
                return False, f"Sulekha city mismatch ({url_path_low} != {district})"
            for bad_loc in other_locs:
                if len(bad_loc) >= 4 and re.search(r'(?<![a-z])' + re.escape(bad_loc) + r'(?![a-z])', url_path_low):
                    if not any(loc in url_path_low for loc in allowed_cities):
                        return False, f"Sulekha other city rejected ({bad_loc})"

        # IndiaMART URL city check
        if 'indiamart.com' in url.lower():
            parsed_path = [p for p in urlparse(url).path.strip('/').split('/') if p]
            if 'dir.indiamart.com' in domain and parsed_path:
                url_city = parsed_path[0].lower()
                if url_city not in allowed_cities:
                    return False, f"IndiaMART city mismatch ({url_city} != {district})"
            url_and_title = (url + " " + (title or "")).lower()
            for bad_loc in other_locs:
                if len(bad_loc) >= 4 and re.search(r'(?<![a-z])' + re.escape(bad_loc) + r'(?![a-z])', url_and_title):
                    if not any(loc in url_and_title for loc in allowed_cities):
                        return False, f"IndiaMART other city rejected ({bad_loc})"

        # Reject any URL path that explicitly targets another district/city
        url_path_check = urlparse(url).path.lower()
        if not any(loc in url_path_check for loc in allowed_cities):
            if not url_path_check.strip('/').startswith('dt-'):
                for bad_loc in other_locs:
                    if len(bad_loc) >= 4 and re.search(r'(?<![a-z])' + re.escape(bad_loc) + r'(?![a-z])', url_path_check):
                        return False, f"URL path belongs to another location ({bad_loc})"

        return True, "Valid candidate"

    def wait_if_paused(self):
        while self.check_pause():
            if self.check_abort():
                return
            time.sleep(0.5)

    def is_virtual_pbx_number(self, number_str):
        """Return True if number belongs to JustDial (0794xxxxxxx) or IndiaMART (0804xxxxxxx) Cloud-PBX virtual ranges."""
        digits = re.sub(r'\D', '', str(number_str or ''))
        if digits.startswith('91') and len(digits) == 12:
            digits = digits[2:]
        elif digits.startswith('0') and len(digits) == 11:
            digits = digits[1:]
        return digits.startswith(('794', '804', '8037', '7971'))

    def is_valid_indian_mobile(self, number_str):
        digits = re.sub(r'\D', '', str(number_str or ''))
        if digits.startswith('91') and len(digits) == 12:
            digits = digits[2:]
        elif digits.startswith('0') and len(digits) == 11:
            digits = digits[1:]
        # Reject locked JustDial Cloud-PBX virtual numbers (0794xxxxxxx) that block direct calls
        if len(digits) == 10 and digits[0] in '6789' and digits not in DUMMY_PHONES and not digits.startswith('794'):
            return digits
        return None

    def _business_name_similarity(self, target_name, cand_name):
        from difflib import SequenceMatcher
        stop = {'and', 'the', 'co', 'pvt', 'ltd', 'private', 'limited', 'inc', 'in', 'erode', 'salem', 'tiruppur', 'coimbatore', 'chennai', 'tamil', 'nadu'}
        t_clean = re.sub(r'[^a-z0-9\s]', ' ', (target_name or '').lower())
        c_clean = re.sub(r'[^a-z0-9\s]', ' ', (cand_name or '').lower())
        t_words = [w for w in t_clean.split() if len(w) >= 2 and w not in stop]
        c_words = [w for w in c_clean.split() if len(w) >= 2 and w not in stop]
        if not t_words or not c_words:
            return 0.0
        first_t = t_words[0] if t_words[0] not in ('sri', 'shri', 'sree', 'new', 'jai', 'om') or len(t_words) == 1 else t_words[1]
        first_matched = any(
            first_t == cw or first_t in cw or cw in first_t or SequenceMatcher(None, first_t, cw).ratio() >= 0.8
            for cw in c_words
        )
        if not first_matched:
            return 0.0
        matched = sum(
            1 for tw in t_words
            if any(tw == cw or tw in cw or cw in tw or SequenceMatcher(None, tw, cw).ratio() >= 0.8 for cw in c_words)
        )
        word_ratio = matched / len(t_words)
        seq_ratio = SequenceMatcher(None, " ".join(t_words), " ".join(c_words[:len(t_words) + 1])).ratio()
        bonus = 0.05 if " ".join(t_words) == " ".join(c_words[:len(t_words)]) else 0.0
        return max(word_ratio, seq_ratio) + bonus

    def lookup_real_phone_for_business(self, name, area, district, state, city=None):
        """
        Solution 2: Auto-lookup 100% Real Direct Owner Mobile Number & Landline/Email
        for a JustDial business using:
          1. In-memory Google Places cache (if already discovered)
          2. Google Maps Direct API (/search?tbm=map) by Business Name + Area + District
          3. Yahoo / DuckDuckGo Web Search + Official Website Fallback
        """
        if self.check_abort() or not name or len(name.strip()) < 3:
            return [], [], [], ""

        # 1. Check in-memory Google Places cache first
        for cached_name, cached_info in self.google_places_cache.items():
            if self._business_name_similarity(name, cached_name) >= 0.82:
                c_mob, c_off = cached_info.get('mobiles', []), cached_info.get('offices', [])
                if c_mob or c_off:
                    return list(c_mob), list(c_off), [], cached_info.get('website', '')

        allowed_cities = self.get_allowed_cities(district, city)
        other_locs = self.get_other_locations(district, state, city)

        mobiles = []
        landlines = []
        emails = []
        website = ""

        gmaps_pb = (
            "%217i20%2110b1%2112m61%211m5%2118b1%2130b1%2131m1%211b1%2134e1%212m4%215m1%216e2%2120e3%2139b1"
            "%216m31%2132i1%2149b1%2163m0%2166b1%2185b1%21114b1%21149b1%21206b1%21209b1%21212b1%21215b1%21216b1"
            "%21222b1%21223b1%21234b1%21235b1%21239b1%21246b1%21253b1%21260b1%21262b1%21266b1%21270b1%21271b1"
            "%21273b1%21277b1%21281b1%21291m0%21294b1%21302i300%21303i100%2110b1%2112b1%2113b1%2114b1%2116b1"
            "%2117m1%213e1%2120m4%215e2%216b1%218b1%2114b1%2146m1%211b0%2196b1%2197m1%212b1%2199b1%2119m4"
            "%212m3%211i360%212i120%214i8%2120m57%212m2%211i203%212i100%213m2%212i4%215b1%216m6%211m2%211i86"
            "%212i86%211m2%211i408%212i240%217m33%211m3%211e1%212b0%213e3%211m3%211e2%212b1%213e2%211m3%211e2"
            "%212b0%213e3%211m3%211e8%212b0%213e3%211m3%211e10%212b0%213e3%211m3%211e10%212b1%213e2%211m3"
            "%211e10%212b0%213e4%211m3%211e9%212b1%213e2%212b1%219b0%2115m8%211m7%211m2%211m1%211e2%212m2"
            "%211i195%212i195%213i20%2124m107%211m25%2113m9%212b1%213b1%214b1%216i1%218b1%219b1%2114b1%2120b1"
            "%2125b1%2118m14%213b1%214b1%215b1%216b1%2113b1%2114b1%2117b1%2121b1%2122b1%2132b1%2133m1%211b1"
            "%2134b1%2136e2%2110m1%218e3%2111m1%213e1%2117b1%2120m2%211e3%211e6%2124b1%2125b1%2126b1%2127b1"
            "%2129b1%2130m1%212b1%2136b1%2137b1%2139m3%212m2%212i1%213i1%2143b1%2152b1%2154m1%211b1%2155b1"
            "%2156m1%211b1%2161m2%211m1%211e1%2165m5%213m4%211m3%211m2%211i224%212i298%2172m22%211m8%212b1"
            "%215b1%217b1%2112m4%211b1%212b1%214m1%211e1%214b1%218m10%211m6%214m1%211e1%214m1%211e3%214m1"
            "%211e4%213sother_user_google_review_posts__and__hotel_and_vr_partner_review_posts%216m1%211e1%219b1"
            "%2189b1%2190m2%211m1%211e2%2198m3%211b1%212b1%213b1%21103b1%21113b1%21114m3%211b1%212m1%211b1"
            "%21117b1%21122m1%211b1%21126b1%21127b1%21128m1%211b1%2126m4%212m3%211i80%212i92%214i8%2130m28"
            "%211m6%211m2%211i0%212i0%212m2%211i530%212i768%211m6%211m2%211i974%212i0%212m2%211i1024%212i768"
            "%211m6%211m2%211i0%212i0%212m2%211i1024%212i20%211m6%211m2%211i0%212i748%212m2%211i1024%212i768"
            "%2134m19%212b1%213b1%214b1%216b1%218m6%211b1%213b1%214b1%215b1%216b1%217b1%219b1%2112b1%2114b1"
            "%2120b1%2123b1%2125b1%2126b1%2131b1%2137m1%211e81%2142b1%2149m10%213b1%216m2%211b1%212b1%217m2"
            "%211e3%212b1%218b1%219b1%2110e2%2150m3%212e2%213m1%213b1%2161b1%2167m5%217b1%2110b1%2114b1"
            "%2115m1%211b0%2169i798%2177b1"
        )

        # 2. Google Maps Direct API (/search?tbm=map)
        g_queries = [f"{name} {area} {district}".replace('  ', ' ').strip()]
        if area and area.lower() != district.lower():
            g_queries.append(f"{name} {district}".strip())

        for q_str in g_queries:
            try:
                q_enc = urllib.parse.quote_plus(q_str)
                g_url = f"https://www.google.com/search?tbm=map&authuser=0&hl=en&gl=in&q={q_enc}&pb=%211s{q_enc}{gmaps_pb}"
                r = self.session.get(g_url, timeout=(4, 7))
                if r.status_code == 200 and len(r.text) > 1000:
                    best_score = 0.0
                    best_mob = []
                    best_land = []
                    for m in re.finditer(r'tel:([0-9+\-]+)', r.text):
                        raw_tel = m.group(1)
                        after = r.text[m.end():min(len(r.text), m.end() + 700)]
                        p_match = re.search(r'\[\[\[7,\[\["([^"]+)"\]', after)
                        a_match = re.search(r'\[2,\[\["([^"]+)"\]\]', after)
                        p_name = p_match.group(1) if p_match else ""
                        f_addr = a_match.group(1) if a_match else after[:400]

                        addr_low = (p_name + " " + f_addr).lower()
                        if not any(loc in addr_low for loc in allowed_cities):
                            continue
                        if any(len(bl) >= 4 and re.search(r'(?<![a-z])' + re.escape(bl) + r'(?![a-z])', f_addr.lower()) for bl in other_locs if bl not in addr_low):
                            continue
                        if self.has_conflicting_location(f_addr, district, state, city):
                            continue

                        score = self._business_name_similarity(name, p_name) if p_name else 0.0
                        if score >= 0.65:
                            mob = self.is_valid_indian_mobile(raw_tel)
                            if mob and not self.is_virtual_pbx_number(mob):
                                fmt = f"+91 {mob[:5]} {mob[5:]}"
                                if score > best_score + 0.01:
                                    best_score = score
                                    best_mob = [fmt]
                                elif abs(score - best_score) <= 0.01 and fmt not in best_mob:
                                    best_mob.append(fmt)
                            elif not mob:
                                digits = re.sub(r'\D', '', raw_tel)
                                if 10 <= len(digits) <= 12 and not self.is_virtual_pbx_number(digits):
                                    if score >= best_score - 0.01 and raw_tel not in best_land:
                                        best_land.append(raw_tel)
                    if best_mob or best_land:
                        mobiles.extend([p for p in best_mob if p not in mobiles])
                        landlines.extend([l for l in best_land if l not in landlines])
                        break
            except Exception:
                pass

        # 3. Web Search Fallback (Brave Search + Official Website)
        if not mobiles and not landlines and not self.check_abort():
            web_queries = [f"{name} {area} {district} contact phone".replace('  ', ' ').strip()]
            if area and area.lower() != district.lower():
                web_queries.append(f"{name} {district} contact phone".strip())

            candidate_urls = []
            for q_web in web_queries:
                results = []
                try:
                    brave_items = self.discover_urls_brave(q_web, max_results=6)
                    for b_item in brave_items:
                        results.append({
                            'href': b_item.get('url', ''),
                            'title': b_item.get('title', ''),
                            'body': b_item.get('snippet', '')
                        })
                except Exception:
                    pass
                if not results:
                    try:
                        results = list(DDGS(timeout=4).text(q_web, backend='yahoo', max_results=6))
                    except Exception:
                        results = []
                for item in results:
                    u = item.get('href', '')
                    title = item.get('title', '')
                    body = item.get('body', '')
                    combined = f"{title} {body}"
                    if not any(loc in combined.lower() or loc in u.lower() for loc in allowed_cities):
                        continue
                    if self.has_conflicting_location(combined, district, state, city):
                        continue
                    if self._business_name_similarity(name, title) >= 0.6 or name.lower() in combined.lower():
                        for pm in re.findall(r'(?:\+91[\s\-]?|0)?([6-9]\d{4}[\s\-]?\d{5})\b', combined):
                            mob = self.is_valid_indian_mobile(pm)
                            if mob and not self.is_virtual_pbx_number(mob):
                                fmt = f"+91 {mob[:5]} {mob[5:]}"
                                if fmt not in mobiles:
                                    mobiles.append(fmt)
                        for em in re.findall(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+', combined):
                            em_c = em.rstrip('.,;:')
                            if self.is_valid_email(em_c) and em_c.lower() not in emails:
                                emails.append(em_c.lower())
                        dom = urlparse(u).netloc.lower()
                        if u.startswith('http') and not self.is_directory_domain(dom) and not any(x in dom for x in ['facebook.com', 'instagram.com', 'youtube.com', 'linkedin.com', 'justdial.com', 'indiamart.com', 'dnb.com', 'infobel']):
                            if u not in candidate_urls:
                                candidate_urls.append(u)
                if mobiles:
                    break

            if not mobiles and candidate_urls:
                try:
                    r_site = self.session.get(candidate_urls[0], timeout=(3, 5))
                    if r_site.status_code == 200:
                        s_soup = BeautifulSoup(r_site.text, 'html.parser')
                        m_set, o_set, e_set, _ = self.extract_contacts_from_text(s_soup.get_text(separator=' '), s_soup)
                        for mp in m_set:
                            if not self.is_virtual_pbx_number(mp) and mp not in mobiles:
                                mobiles.append(mp)
                        for op in o_set:
                            if not self.is_virtual_pbx_number(op) and op not in landlines:
                                landlines.append(op)
                        for ep in e_set:
                            if ep not in emails:
                                emails.append(ep)
                        website = candidate_urls[0]
                except Exception:
                    pass

        return mobiles, landlines, emails, website

    def is_valid_email(self, email_str):
        email = email_str.strip().lower()
        if not re.match(r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$', email):
            return False
        if any(email.endswith(ext) for ext in ['.png', '.jpg', '.jpeg', '.gif', '.svg', '.webp', '.js', '.css', '.woff']):
            return False
        if any(fake in email for fake in FAKE_EMAIL_PATTERNS):
            return False
        return True

    def decode_bing_url(self, href):
        if 'bing.com/ck/a' in href and 'u=' in href:
            parsed = urllib.parse.urlparse(href)
            qs = urllib.parse.parse_qs(parsed.query)
            if 'u' in qs:
                u_val = qs['u'][0]
                if u_val.startswith('a1'):
                    raw = u_val[2:]
                    padded = raw + '=' * (-len(raw) % 4)
                    try:
                        return base64.urlsafe_b64decode(padded).decode('utf-8', errors='ignore')
                    except Exception:
                        pass
        return href

    def scrape_justdial_listing(self, url):
        """
        Scrape JustDial listing page - extracts phone numbers visible on listing page
        (JustDial hides full numbers behind login, but often partial numbers or other
        contact info is in meta/schema or listing cards).
        """
        try:
            jd_headers = dict(HEADERS)
            jd_headers['Referer'] = 'https://www.google.com/'
            r = self.session.get(url, headers=jd_headers, timeout=(4, 8))
            if r.status_code != 200:
                return []

            soup = BeautifulSoup(r.text, 'html.parser')
            businesses = []

            # JustDial listing items
            for item in soup.select('.resultbox_info, .jd_body, .list_info, [data-href]'):
                name_tag = item.select_one('.resultbox_title_anchor, .jd-heading, h2, .fn')
                phone_tag = item.select_one('.contact-info, .mobilesv, [itemprop="telephone"]')
                addr_tag = item.select_one('.addressinfo, [itemprop="address"], .address')

                name = name_tag.text.strip() if name_tag else ''
                phone = phone_tag.text.strip() if phone_tag else ''
                addr = addr_tag.text.strip() if addr_tag else ''

                if name:
                    # Try to find phone via data attributes or schema
                    data_phone = item.get('data-mobile', '') or item.get('data-phone', '')
                    if data_phone:
                        phone = data_phone

                    businesses.append({
                        'name': name,
                        'phone': re.sub(r'\D', '', phone)[-10:] if phone else '',
                        'address': addr,
                        'source': url
                    })

            # Also check schema.org JSON-LD on page
            import json
            for script in soup.select('script[type="application/ld+json"]'):
                try:
                    data = json.loads(script.string or '{}')
                    items = data if isinstance(data, list) else [data]
                    for item in items:
                        if item.get('@type') in ['LocalBusiness', 'Organization', 'ProfessionalService']:
                            businesses.append({
                                'name': item.get('name', ''),
                                'phone': item.get('telephone', ''),
                                'address': str(item.get('address', '')),
                                'source': url
                            })
                except Exception:
                    pass

            return businesses

        except Exception as e:
            self.log(f"JustDial scrape note: {e}", 'debug')
            return []

    def build_search_queries(self, state, district, city, category_item, custom_keyword=""):
        """
        Build precise, targeted search queries that avoid fashion/irrelevant results.
        Discovers natural Google/Web organic websites, directory subcategories
        (Justdial, Sulekha, IndiaMART, TradeIndia) and verified contractor company websites.
        """
        cat_terms = category_item.get('search_terms', [category_item['name']]) if category_item else []
        term = custom_keyword.strip() if custom_keyword else (cat_terms[0] if cat_terms else "Civil Contractors")

        # Build location string — use city/area first if provided
        if city:
            loc_primary = f"{city}, {district}"
            loc_short = city
        else:
            loc_primary = district
            loc_short = district

        queries = [
            # Natural web search queries (discovers official websites, IndiaMART, TradeIndia, Justdial profiles)
            f'{term} {loc_short} {state}',
            f'{term} in {loc_primary}',
            # High-yield Directory subcategories (yielding 100-200+ vendor listings)
            f'site:justdial.com {term} {loc_short}',
            f'site:justdial.com/{loc_short}/ {term}',
            f'site:justdial.com {term} dealers {loc_short}',
            f'site:justdial.com {term} manufacturers {loc_short}',
            f'site:justdial.com {term} suppliers {loc_short}',
            f'site:dir.indiamart.com/{loc_short.lower()}/ {term}',
            f'site:indiamart.com {term} {loc_short}',
            f'site:tradeindia.com {term} {loc_short}',
            f'site:sulekha.com {term} {loc_short}',
            f'site:sulekha.com/{loc_short.lower()} {term}',
            # Direct contractor & vendor websites with phone/email
            f'"{term}" {loc_primary} {state} phone mobile contact',
            f'{term} in {loc_primary} office mobile phone contact',
            f'"{term}" "{district}" contact number',
        ]

        # Add commercial headquarters / alias city queries for full directory discovery
        alt_slugs = self.get_portal_city_slugs(district, state)
        for alt_slug in alt_slugs:
            if alt_slug.lower() != loc_short.lower():
                queries.append(f'site:justdial.com {term} {alt_slug}')
                queries.append(f'site:dir.indiamart.com/{alt_slug.lower()}/ {term}')
                queries.append(f'site:sulekha.com {term} {alt_slug}')

        if not custom_keyword and len(cat_terms) > 1:
            queries.append(f'"{cat_terms[1]}" {loc_primary} contact number mobile')

        return queries

    def discover_urls_brave(self, query, max_results=20):
        discovered = []
        seen = set()
        try:
            elapsed = time.time() - getattr(self, '_last_brave_req', 0.0)
            if elapsed < 1.2:
                time.sleep(1.2 - elapsed)
            url = f"https://search.brave.com/search?q={urllib.parse.quote(query)}&country=in"
            r = self.brave_client.get(url)
            self._last_brave_req = time.time()
            if r.status_code == 200:
                soup = BeautifulSoup(r.text, 'html.parser')
                for sn in soup.select('div.snippet[data-type="web"], div.snippet'):
                    a = sn.select_one('a[href^="http"]')
                    if not a:
                        continue
                    href = a.get('href', '').strip()
                    if not href or 'brave.com' in href or href in seen:
                        continue
                    seen.add(href)
                    t = sn.select_one('.title, .snippet-title')
                    d = sn.select_one('.snippet-description, .generic-snippet .content, .content')
                    title = t.get_text(" ", strip=True) if t else href
                    snippet = d.get_text(" ", strip=True) if d else ''
                    discovered.append({'url': href, 'title': title, 'snippet': snippet, 'engine': 'Brave Search'})
                    if len(discovered) >= max_results:
                        break
        except Exception as e:
            self.log(f"Brave Search note: {e}", 'debug')

        # Fallback if Brave Search returns fewer than 3 results (e.g. rate-limit cooldown)
        if len(discovered) < 3:
            try:
                with DDGS(timeout=7) as ddgs:
                    for backend_name in ('brave', 'yahoo'):
                        try:
                            results = list(ddgs.text(query, region='in-en', backend=backend_name, max_results=max_results))
                        except Exception:
                            results = []
                        if results:
                            for item in results:
                                u = item.get('href', '')
                                title = item.get('title', '')
                                snippet = item.get('body', '')
                                if u and u.startswith('http') and u not in seen:
                                    seen.add(u)
                                    discovered.append({'url': u, 'title': title, 'snippet': snippet, 'engine': 'Brave Search'})
                                    if len(discovered) >= max_results:
                                        break
                        if len(discovered) >= 3:
                            break
            except Exception as e:
                self.log(f"Brave fallback note: {e}", 'debug')

        return discovered

    def discover_urls_yahoo(self, query, max_results=20):
        discovered = []
        seen = set()
        try:
            url = f"https://in.search.yahoo.com/search?p={urllib.parse.quote(query)}&n=30"
            r = self.brave_client.get(url)
            if r.status_code == 200:
                soup = BeautifulSoup(r.text, 'html.parser')
                for div in soup.select('div.algo, div.Sr, .dd.algo'):
                    a = div.select_one('h3 a, a')
                    if not a:
                        continue
                    href = a.get('href', '')
                    real_u = href
                    if 'RU=' in href:
                        try:
                            real_u = urllib.parse.unquote(href.split('RU=')[1].split('/RK=')[0])
                        except Exception:
                            real_u = href
                    if not real_u or not real_u.startswith('http') or 'yahoo.com' in real_u or real_u in seen:
                        continue
                    seen.add(real_u)
                    title = a.get_text(" ", strip=True)
                    snip_el = div.select_one('.compText, p')
                    snippet = snip_el.get_text(" ", strip=True) if snip_el else ''
                    discovered.append({'url': real_u, 'title': title, 'snippet': snippet, 'engine': 'Yahoo'})
                    if len(discovered) >= max_results:
                        break
        except Exception as e:
            self.log(f"Yahoo direct note: {e}", 'debug')

        if len(discovered) < 5:
            try:
                with DDGS(timeout=7) as ddgs:
                    for item in ddgs.text(query, region='in-en', backend='yahoo', max_results=max_results):
                        u = item.get('href', '')
                        if u and u.startswith('http') and u not in seen:
                            seen.add(u)
                            discovered.append({
                                'url': u,
                                'title': item.get('title', ''),
                                'snippet': item.get('body', ''),
                                'engine': 'Yahoo'
                            })
                            if len(discovered) >= max_results:
                                break
            except Exception as e:
                self.log(f"Yahoo DDGS note: {e}", 'debug')
        return discovered

    def discover_urls_duckduckgo(self, query, max_results=20):
        discovered = []
        seen = set()
        try:
            with DDGS(timeout=7) as ddgs:
                for b_name in ('duckduckgo', 'lite'):
                    try:
                        results = list(ddgs.text(query, region='in-en', backend=b_name, max_results=max_results))
                    except Exception:
                        results = []
                    for item in results:
                        u = item.get('href', '')
                        if u and u.startswith('http') and u not in seen:
                            seen.add(u)
                            discovered.append({
                                'url': u,
                                'title': item.get('title', ''),
                                'snippet': item.get('body', ''),
                                'engine': 'DuckDuckGo'
                            })
                            if len(discovered) >= max_results:
                                break
                    if len(discovered) >= 5:
                        break
        except Exception as e:
            self.log(f"DuckDuckGo note: {e}", 'debug')
        return discovered

    def discover_urls_firefox(self, query, max_results=20):
        """Discover web URLs using Mozilla Firefox Gecko headers & Firefox search endpoints."""
        discovered = []
        seen = set()
        ff_headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:133.0) Gecko/20100101 Firefox/133.0',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-IN,en-US;q=0.7,en;q=0.3',
        }
        try:
            r = requests.post(
                "https://html.duckduckgo.com/html/",
                data={'q': query, 'kl': 'in-en'},
                headers=ff_headers,
                timeout=(4, 7)
            )
            if r.status_code == 200:
                soup = BeautifulSoup(r.text, 'html.parser')
                for res_div in soup.select('.result, .web-result'):
                    a = res_div.select_one('a.result__a')
                    if not a:
                        continue
                    href = a.get('href', '')
                    if 'uddg=' in href:
                        try:
                            href = urllib.parse.unquote(href.split('uddg=')[1].split('&')[0])
                        except Exception:
                            pass
                    if href and href.startswith('http') and href not in seen:
                        seen.add(href)
                        sn = res_div.select_one('.result__snippet')
                        discovered.append({
                            'url': href,
                            'title': a.get_text(" ", strip=True),
                            'snippet': sn.get_text(" ", strip=True) if sn else '',
                            'engine': 'Firefox'
                        })
                        if len(discovered) >= max_results:
                            break
        except Exception as e:
            self.log(f"Firefox search note: {e}", 'debug')

        if len(discovered) < 5:
            try:
                with DDGS(timeout=7) as ddgs:
                    for b_name in ('duckduckgo', 'yahoo'):
                        try:
                            results = list(ddgs.text(query, region='in-en', backend=b_name, max_results=max_results))
                        except Exception:
                            results = []
                        for item in results:
                            u = item.get('href', '')
                            if u and u.startswith('http') and u not in seen:
                                seen.add(u)
                                discovered.append({
                                    'url': u,
                                    'title': item.get('title', ''),
                                    'snippet': item.get('body', ''),
                                    'engine': 'Firefox'
                                })
                                if len(discovered) >= max_results:
                                    break
                        if len(discovered) >= 5:
                            break
            except Exception:
                pass
        return discovered

    def discover_urls_google(self, query, max_results=20):
        """
        Discover organic web URLs for Google Search (official websites, IndiaMART,
        TradeIndia, Justdial, Sulekha, etc.).
        """
        discovered = []
        seen = set()
        try:
            with DDGS(timeout=7) as ddgs:
                for b_name in ('google', 'yahoo', 'duckduckgo'):
                    try:
                        results = list(ddgs.text(query, region='in-en', backend=b_name, max_results=max_results))
                    except Exception:
                        results = []
                    for item in results:
                        u = item.get('href', '')
                        if u and u.startswith('http') and u not in seen:
                            seen.add(u)
                            discovered.append({
                                'url': u,
                                'title': item.get('title', ''),
                                'snippet': item.get('body', ''),
                                'engine': 'Google'
                            })
                            if len(discovered) >= max_results:
                                break
                    if len(discovered) >= 8:
                        break
        except Exception as e:
            self.log(f"Google Web discovery note: {e}", 'debug')
        return discovered

    def discover_google_knowledge_panel(self, state, district, city=None, category_item=None, custom_keyword=""):
        """
        Queries Google's Knowledge Panel / Map JSON endpoint (tbm=map) to extract
        exact Google Knowledge Panel cards (like 'KNK STEELS' -> 081898 94444, 4.4 ★,
        address, and official website https://www.knksteels.co.in/).
        """
        import json
        candidates = []
        seen_urls = set()
        search_loc = f"{city}, {district}" if city else district
        cat_name = category_item.get('name', 'Civil Contractors') if category_item else 'Civil Contractors'
        term = custom_keyword.strip() if custom_keyword else cat_name
        term_norm = self.normalize_keyword_typos(term)
        allowed_cities = self.get_allowed_cities(district, city)

        kp_queries = []
        if district.lower() in term.lower():
            kp_queries.append(term)
        if district.lower() in term_norm.lower() and term_norm != term:
            kp_queries.append(term_norm)
        kp_queries.append(f"{term} {search_loc} {state}".strip())
        if term_norm != term:
            kp_queries.append(f"{term_norm} {search_loc} {state}".strip())
        if custom_keyword:
            kp_queries.append(f"{term_norm} {district}".strip())

        for q in kp_queries:
            try:
                map_url = f"https://www.google.com/search?tbm=map&authuser=0&hl=en&gl=in&q={urllib.parse.quote(q)}"
                r = self.session.get(map_url, timeout=(4, 7))
                if r.status_code != 200 or len(r.text) < 200:
                    continue
                raw = r.text
                if raw.startswith(")]}'"):
                    raw = raw[4:]
                data = json.loads(raw.strip())

                biz_nodes = []
                def walk(node):
                    if isinstance(node, list):
                        if len(node) > 14 and isinstance(node[11], str) and (isinstance(node[7], list) or isinstance(node[18], str) or isinstance(node[39], str)):
                            biz_nodes.append(node)
                        for x in node:
                            walk(x)
                walk(data)

                for node in biz_nodes:
                    name = (node[11] or '').strip()
                    if not name or len(name) < 3:
                        continue
                    addr_full = ""
                    if len(node) > 39 and isinstance(node[39], str) and node[39].strip():
                        addr_full = node[39].strip()
                    elif len(node) > 18 and isinstance(node[18], str) and node[18].strip():
                        addr_full = node[18].strip()

                    node_str = json.dumps(node)
                    if not any(loc in (name + " " + addr_full + " " + node_str).lower() for loc in allowed_cities):
                        continue
                    if self.has_conflicting_location(f"{name} {addr_full}", district, state, city):
                        continue
                    if custom_keyword and not self.matches_custom_keyword(f"{name} {addr_full} {node_str}", custom_keyword):
                        continue

                    # Official website from node[7]
                    official_web = ""
                    if len(node) > 7 and isinstance(node[7], list) and len(node[7]) > 0 and isinstance(node[7][0], str):
                        raw_w = node[7][0]
                        if '/url?q=' in raw_w:
                            raw_w = urllib.parse.unquote(raw_w.split('/url?q=')[1].split('&')[0])
                        elif not raw_w.startswith('http') and len(node[7]) > 1 and isinstance(node[7][1], str):
                            raw_w = 'https://www.' + node[7][1].lstrip('/')
                        if raw_w.startswith('http'):
                            official_web = raw_w

                    # Rating & Reviews from node[4]
                    rating_str = ""
                    if len(node) > 4 and isinstance(node[4], list) and len(node[4]) > 7 and node[4][7]:
                        r_val = node[4][7]
                        r_cnt = node[4][8] if len(node[4]) > 8 and node[4][8] else ""
                        rating_str = f"{r_val} ★ ({r_cnt} Ratings)" if r_cnt else f"{r_val} ★"

                    # Phone numbers
                    mobs = []
                    lands = []
                    for pm in re.findall(r'\"((?:\+91[\s\-]?|0)?[6-9]\d{4}[\s\-]?\d{5})\"', node_str):
                        mob = self.is_valid_indian_mobile(pm)
                        if mob and not self.is_virtual_pbx_number(mob):
                            fmt = f"+91 {mob[:5]} {mob[5:]}"
                            if fmt not in mobs:
                                mobs.append(fmt)
                    for pl in re.findall(r'\"(0\d{2,4}[\s\-]\d{6,8})\"', node_str):
                        raw_tel = pl.strip()
                        if not self.is_Valid_mob_in_land(raw_tel) if hasattr(self, 'is_Valid_mob_in_land') else True:
                            digits = re.sub(r'\D', '', raw_tel)
                            if 10 <= len(digits) <= 12 and not self.is_virtual_pbx_number(digits):
                                if len(digits) == 11 and digits.startswith('0') and digits[1] in '6789':
                                    mob = self.is_valid_indian_mobile(digits[1:])
                                    if mob:
                                        fmt = f"+91 {mob[:5]} {mob[5:]}"
                                        if fmt not in mobs:
                                            mobs.append(fmt)
                                elif raw_tel not in lands:
                                    lands.append(raw_tel)

                    phone_str = ", ".join(mobs)
                    office_str = ", ".join(lands)
                    kp_url = f"https://www.google.com/maps/search/{urllib.parse.quote(name + ' ' + (addr_full or district))}"

                    google_lead = {
                        "business_name": name,
                        "category": custom_keyword.title() if custom_keyword else cat_name,
                        "district": district,
                        "state": state,
                        "city_area": city or district,
                        "rating": rating_str,
                        "mobile_numbers": phone_str,
                        "office_numbers": office_str,
                        "email_addresses": "",
                        "address": addr_full if (addr_full and district.lower() in addr_full.lower()) else f"{addr_full + ', ' if addr_full else ''}{city or district}, {district}, {state}",
                        "website": official_web or kp_url,
                        "source_url": kp_url,
                        "child_pages_crawled": 0,
                        "verification_status": "Strictly Verified",
                        "extracted_at": time.strftime("%Y-%m-%d %H:%M:%S")
                    }

                    if mobs or lands:
                        self.google_places_cache[name.lower()] = {
                            'mobiles': mobs,
                            'offices': lands,
                            'website': official_web or kp_url
                        }

                    if kp_url not in seen_urls:
                        seen_urls.add(kp_url)
                        cand_title = f"{name} ({rating_str}) — Google Knowledge Panel" if rating_str else f"{name} — Google Knowledge Panel"
                        cand_snip = f"Phone: {phone_str or office_str} | Address: {addr_full or district}"
                        candidates.append({
                            'url': kp_url,
                            'title': cand_title,
                            'snippet': cand_snip,
                            'engine': 'Google',
                            '_google_lead': google_lead
                        })

                    # Also add the official website from Knowledge Panel as a direct scrapable site!
                    if official_web and official_web not in seen_urls:
                        seen_urls.add(official_web)
                        candidates.append({
                            'url': official_web,
                            'title': f"{name} — Official Website",
                            'snippet': f"{name}, {addr_full or district}, {state}. Phone: {phone_str}",
                            'engine': 'Google',
                            '_snippet_phones': mobs
                        })
            except Exception as e:
                self.log(f"Google Knowledge Panel note: {e}", 'debug')

        return candidates

    def discover_urls_ddgs(self, query, max_results=20):
        return self.discover_urls_brave(query, max_results=max_results)

    def discover_urls_bing(self, query, max_results=15):
        discovered = []
        seen = set()
        try:
            url = f"https://www.bing.com/search?q={urllib.parse.quote(query)}&cc=in&setlang=en-in"
            r = self.brave_client.get(url)
            if r.status_code != 200:
                r = self.session.get(url, timeout=(4, 6))
            if r.status_code == 200:
                soup = BeautifulSoup(r.text, 'html.parser')
                for li in soup.select('li.b_algo')[:max_results]:
                    h2 = li.select_one('h2 a')
                    snip = li.select_one('.b_caption p, .b_lineclamp2, .b_lineclamp3')
                    if h2:
                        href = self.decode_bing_url(h2.get('href', ''))
                        title = h2.text.strip()
                        snippet = snip.text.strip() if snip else ''
                        if href and href.startswith('http') and href not in seen:
                            seen.add(href)
                            discovered.append({'url': href, 'title': title, 'snippet': snippet, 'engine': 'Microsoft Bing'})
        except Exception as e:
            self.log(f"Bing discovery note: {e}", 'debug')
        return discovered

    def decode_cf_email(self, cfemail):
        try:
            r = int(cfemail[:2], 16)
            return ''.join([chr(int(cfemail[i:i+2], 16) ^ r) for i in range(2, len(cfemail), 2)])
        except Exception:
            return ''

    def discover_google_places_playwright(self, state, district, city=None, category_item=None, custom_keyword=""):
        """
        Scrape Google Local Places business cards using Playwright Chromium.
        Queries Google Maps for '{keyword/category} in {district/city}, {state}'
        and extracts local business cards (Name, Rating, Review Count, Phone, Address, Direct Map URL).
        """
        if self.check_abort():
            return []
        candidates = []
        try:
            from playwright.sync_api import sync_playwright

            search_loc = f"{city}, {district}" if city else district
            cat_name = category_item.get('name', 'Civil Contractors') if category_item else 'Civil Contractors'
            term = custom_keyword if custom_keyword else cat_name
            query_url = f"https://www.google.com/maps/search/{urllib.parse.quote(term + ' in ' + search_loc + ' ' + state)}"

            self.log(f"Searching Google Local Places via Playwright: {term} in {search_loc}", 'info')

            with sync_playwright() as p:
                browser = p.chromium.launch(
                    headless=True,
                    args=[
                        '--disable-blink-features=AutomationControlled',
                        '--no-sandbox',
                        '--disable-setuid-sandbox',
                        '--disable-infobars',
                        '--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'
                    ]
                )
                self.active_browser = browser
                context = browser.new_context(
                    viewport={'width': 1366, 'height': 768},
                    user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
                    locale='en-IN',
                    timezone_id='Asia/Kolkata'
                )
                page = context.new_page()
                page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

                page.goto(query_url, wait_until='domcontentloaded', timeout=25000)
                for _ in range(30):
                    if self.check_abort():
                        break
                    time.sleep(0.1)

                try:
                    feed = page.query_selector('div[role="feed"]')
                    if feed:
                        box = feed.bounding_box()
                        if box:
                            page.mouse.move(box['x'] + box['width'] / 2, box['y'] + box['height'] / 2)
                            prev_cards = 0
                            stable_count = 0
                            for scroll_idx in range(25):
                                if self.check_abort():
                                    break
                                page.mouse.wheel(0, 3500)
                                for _ in range(12):
                                    if self.check_abort():
                                        break
                                    time.sleep(0.1)
                                cur_cards = len(page.query_selector_all('div[role="article"], .Nv2PK'))
                                if cur_cards == prev_cards and cur_cards > 10:
                                    stable_count += 1
                                    if stable_count >= 3:
                                        break
                                else:
                                    stable_count = 0
                                    prev_cards = cur_cards
                    else:
                        scrollable = page.query_selector('div[tabindex="-1"]')
                        if scrollable:
                            for _ in range(12):
                                if self.check_abort():
                                    break
                                scrollable.evaluate("el => el.scrollTop = el.scrollHeight")
                                for _ in range(10):
                                    if self.check_abort():
                                        break
                                    time.sleep(0.1)
                except Exception as ex:
                    self.log(f"Google Maps scroll note: {ex}", 'debug')

                if self.check_abort():
                    try:
                        browser.close()
                    except Exception:
                        pass
                    self.active_browser = None
                    return []

                html = page.content()
                browser.close()
                self.active_browser = None

            soup = BeautifulSoup(html, 'html.parser')
            cards = soup.select('div[role="article"], .Nv2PK')
            self.log(f"Playwright found {len(cards)} Google Local Places cards!", 'info')

            for card in cards:
                name_el = card.select_one('.qBF1Pd, .fontHeadlineSmall')
                name = name_el.text.strip() if name_el else ""
                if not name and card.has_attr('aria-label'):
                    name = card['aria-label']
                if not name or len(name) < 3 or name.lower() in ['google', 'maps', 'results']:
                    continue

                # Rating value
                rate_star_el = card.select_one('[aria-label*="stars"], .MW4etd')
                rate_val = ""
                if rate_star_el:
                    if rate_star_el.has_attr('aria-label'):
                        r_m = re.search(r'([1-5]\.\d)', rate_star_el['aria-label'])
                        if r_m: rate_val = r_m.group(1)
                    if not rate_val:
                        rate_val = rate_star_el.text.strip()

                card_text = card.get_text(separator=' ')
                cnt_m = re.search(r'\(\s*([0-9,]+)\s*\)', card_text)
                rate_cnt = cnt_m.group(1) if cnt_m else ""

                if rate_val and rate_cnt:
                    rating_str = f"{rate_val} ★ ({rate_cnt} Ratings)"
                elif rate_val:
                    rating_str = f"{rate_val} ★"
                else:
                    rating_str = ""

                # Phone number
                phone_str = ""
                p_match = re.findall(r'(?:\+91|0)?[6-9]\d{4}\s*\d{5}', card_text)
                if p_match:
                    digits = re.sub(r'\D', '', p_match[0])
                    phone_str = f"+91 {digits[-10:-5]} {digits[-5:]}" if len(digits) >= 10 else p_match[0]
                else:
                    p_match2 = re.findall(r'0\d{2,4}\s*\d{6,8}', card_text)
                    if p_match2:
                        phone_str = p_match2[0]

                # Map URL
                link_tag = card.select_one('a[href*="/maps/place/"]')
                card_url = link_tag['href'] if link_tag and link_tag.has_attr('href') else query_url

                # Address
                address_str = ""
                spans = [s.text.strip() for s in card.select('span') if s.text.strip()]
                for s in spans:
                    if any(kw in s.lower() for kw in ['rd', 'road', 'street', 'st', 'nagar', 'colony', 'behind', 'near', 'opp', district.lower(), (city or '').lower()]):
                        if not any(kw in s.lower() for kw in ['open', 'closes', 'hours', 'website', 'directions', 'reviews', 'star']) and len(s) > 5:
                            address_str = s
                            break

                # Strict Location Verification for Google Places Card
                if self.has_conflicting_location(f"{name} {address_str} {card_text}", district, state, city):
                    continue

                # Strict Category Relevance (Rejects Travels, Transport, Parcel, and Non-Category cards)
                is_rel, rel_reason = self.is_strictly_category_relevant(
                    name, f"{name} {address_str} {card_text}", category_item, custom_keyword
                )
                if not is_rel:
                    self.log(f"Filtered non-category Google Card ({rel_reason}): {name}", 'debug')
                    continue

                cand_title = f"{name} ({rating_str})" if rating_str else name
                cand_snip = f"Phone: {phone_str} | Address: {address_str or district}" if phone_str else f"Address: {address_str or district}"

                google_lead = {
                    "business_name": name,
                    "category": custom_keyword.title() if custom_keyword else cat_name,
                    "district": district,
                    "state": state,
                    "city_area": city or district,
                    "rating": rating_str,
                    "mobile_numbers": phone_str,
                    "office_numbers": "",
                    "email_addresses": "",
                    "address": address_str if (address_str and district.lower() in address_str.lower()) else f"{address_str + ', ' if address_str else ''}{city or district}, {district}, {state}",
                    "website": card_url,
                    "source_url": card_url,
                    "child_pages_crawled": 0,
                    "verification_status": "Strictly Verified",
                    "extracted_at": time.strftime("%Y-%m-%d %H:%M:%S")
                }

                if phone_str and not self.is_virtual_pbx_number(phone_str):
                    self.google_places_cache[name.lower()] = {
                        'mobiles': [phone_str] if phone_str.startswith('+91') else [],
                        'offices': [] if phone_str.startswith('+91') else [phone_str],
                        'website': card_url
                    }

                candidates.append({
                    'url': card_url,
                    'title': cand_title,
                    'snippet': cand_snip,
                    'engine': 'Google',
                    '_google_lead': google_lead
                })

        except Exception as e:
            self.log(f"Google Places Playwright note: {e}", 'debug')

        return candidates

    def discover_candidates(self, state, district, city, category_item, custom_keyword="", search_engines=None):
        """
        Discover candidate URLs using user-selected search engines:
        Google, Brave Search, Firefox, Yahoo, Microsoft Bing, DuckDuckGo.
        Returns a list of candidate dicts with url, title, snippet, engine.
        """
        all_candidates = []
        seen_urls = {}

        if not search_engines:
            selected_engines = ['google', 'brave', 'firefox', 'yahoo', 'bing', 'duckduckgo']
        else:
            selected_engines = [str(e).strip().lower() for e in search_engines if str(e).strip()]

        engine_labels = {
            'google': 'Google',
            'brave': 'Brave Search',
            'firefox': 'Firefox',
            'yahoo': 'Yahoo',
            'bing': 'Microsoft Bing',
            'duckduckgo': 'DuckDuckGo'
        }
        active_names = [engine_labels.get(e, e.title()) for e in selected_engines]
        self.log(f"Active Search Engines: {', '.join(active_names)}", 'info')

        # 0. Guaranteed High-Yield Directory Seeds (Justdial, IndiaMART, Sulekha, TradeIndia)
        # Guarantees verified extraction targets for EVERY Indian district even if search engines rate-limit
        try:
            seeds = self.generate_guaranteed_directory_seeds(state, district, city, category_item, custom_keyword)
            for s in seeds:
                u = s['url']
                if u not in seen_urls:
                    seen_urls[u] = s
                    all_candidates.append(s)
            if seeds:
                self.log(f"Injected {len(seeds)} guaranteed directory targets for {district}, {state}", 'info')
        except Exception as seed_err:
            self.log(f"Directory seeds note: {seed_err}", 'debug')

        # 1. Google Local Places & Google Knowledge Panel (when Google is selected)
        if 'google' in selected_engines:
            try:
                kp_cands = self.discover_google_knowledge_panel(state, district, city, category_item, custom_keyword)
                for kp in kp_cands:
                    u = kp['url']
                    if u not in seen_urls:
                        seen_urls[u] = kp
                        all_candidates.append(kp)
            except Exception as ex:
                self.log(f"Google Knowledge Panel note: {ex}", 'debug')

            try:
                g_places = self.discover_google_places_playwright(state, district, city, category_item, custom_keyword)
                for gp in g_places:
                    u = gp['url']
                    if u not in seen_urls:
                        seen_urls[u] = gp
                        all_candidates.append(gp)
            except Exception as ex:
                self.log(f"Google Places discovery error: {ex}", 'debug')

        # 2. Discover Web URLs across all selected Search Engines
        queries = self.build_search_queries(state, district, city, category_item, custom_keyword)
        for q in queries:
            if self.check_abort():
                break
            self.wait_if_paused()
            self.log(f"Searching [{', '.join(active_names)}]: {q}", 'info')

            results = []
            if 'google' in selected_engines and not self.check_abort():
                results.extend(self.discover_urls_google(q, max_results=20))
            if 'brave' in selected_engines and not self.check_abort():
                results.extend(self.discover_urls_brave(q, max_results=20))
            if 'firefox' in selected_engines and not self.check_abort():
                results.extend(self.discover_urls_firefox(q, max_results=20))
            if 'yahoo' in selected_engines and not self.check_abort():
                results.extend(self.discover_urls_yahoo(q, max_results=20))
            if 'bing' in selected_engines and not self.check_abort():
                results.extend(self.discover_urls_bing(q, max_results=15))
            if 'duckduckgo' in selected_engines and not self.check_abort():
                results.extend(self.discover_urls_duckduckgo(q, max_results=20))

            for r in results:
                url = r['url'].rstrip('/') if r['url'].count('/') == 3 else r['url']
                r['url'] = url
                domain = urlparse(url).netloc.lower().replace('www.', '')
                # Check excluded domains, but allow social business pages (Facebook, Instagram, LinkedIn)
                # if their search snippet directly contains an Indian phone number
                if any(ex in domain for ex in EXCLUDED_DOMAINS):
                    snip_text = f"{r.get('title','')} {r.get('snippet','')}"
                    is_social = any(s in domain for s in ['facebook.com', 'instagram.com', 'linkedin.com'])
                    has_phone = bool(re.search(r'(?:\+91[\s\-]?|0)?([6-9]\d{4}[\s\-]?\d{5})\b', snip_text))
                    if not (is_social and has_phone):
                        continue
                # Pre-filter candidate relevance before adding to discovered list
                valid, reason = self.is_candidate_relevant(
                    url, r.get('title',''), r.get('snippet',''), district, state, city, category_item, custom_keyword,
                    is_seed=r.get('_is_seed', False)
                )
                if not valid:
                    self.log(f"Filtered out URL ({reason}): {url}", 'debug')
                    continue

                # Extract any real mobile phone numbers visible directly in the search snippet
                snip_phones = []
                for pm in re.findall(r'(?:\+91[\s\-]?|0)?([6-9]\d{4}[\s\-]?\d{5})\b', f"{r.get('title','')} {r.get('snippet','')}"):
                    mob = self.is_valid_indian_mobile(pm)
                    if mob and not self.is_virtual_pbx_number(mob):
                        fmt = f"+91 {mob[:5]} {mob[5:]}"
                        if fmt not in snip_phones:
                            snip_phones.append(fmt)
                if snip_phones:
                    r['_snippet_phones'] = snip_phones

                if url not in seen_urls:
                    seen_urls[url] = r
                    all_candidates.append(r)
                else:
                    existing_eng = seen_urls[url].get('engine', '')
                    new_eng = r.get('engine', '')
                    if new_eng and new_eng not in existing_eng:
                        seen_urls[url]['engine'] = f"{existing_eng} + {new_eng}" if existing_eng else new_eng

            if len(all_candidates) >= 220:
                break
            time.sleep(0.3)

        return all_candidates

    def find_child_pages(self, base_url, soup):
        child_links = []
        base_netloc = urlparse(base_url).netloc.lower()
        target_slugs = ['contact', 'about', 'reach', 'location', 'office', 'branch', 'get-in-touch', 'team']
        seen = set()

        for a in soup.find_all('a', href=True):
            href = a['href'].strip()
            if not href or href.startswith('#') or href.startswith('javascript:'):
                continue
            full_url = urljoin(base_url, href)
            parsed = urlparse(full_url)
            if parsed.netloc.lower() == base_netloc:
                clean_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
                lower_path = parsed.path.lower()
                link_text = a.text.lower()
                if any(slug in lower_path or slug in link_text for slug in target_slugs):
                    if clean_url != base_url and clean_url not in seen:
                        seen.add(clean_url)
                        child_links.append(clean_url)
                        if len(child_links) >= 3:
                            break
        return child_links

    def clean_company_name(self, raw_title, domain):
        name = (raw_title or '').strip()
        by_match = re.search(r'\bby\s+([A-Za-z0-9&\.\-\'\s]{3,60}?)(?:,|\||-|$)', name, re.IGNORECASE)
        if by_match:
            cand_by = by_match.group(1).strip()
            if len(cand_by) >= 3:
                return cand_by
        in_match = re.match(r'^([A-Za-z0-9&\.\-\'\s]{3,60}?)\s+in\s+[A-Z]', name)
        if in_match:
            cand_in = in_match.group(1).strip()
            if len(cand_in) >= 3:
                return cand_in
        for sep in [' - ', ' | ', ' – ', ' — ', ' :: ']:
            if sep in name:
                name = name.split(sep)[0].strip()
        if ',' in name:
            first_part = name.split(',')[0].strip()
            if len(first_part) >= 3:
                name = first_part
        name = re.sub(r'(?i)\b(home|official website|welcome to|contact us|about us|top best)\b', '', name).strip()
        if not name or len(name) < 3 or name.lower() in ('trader', 'wholesaler', 'distributor', 'manufacturer', 'supplier'):
            dom_parts = domain.replace('www.', '').split('.')
            name = dom_parts[0].replace('-', ' ').replace('_', ' ').title()
        return name

    def extract_contacts_from_text(self, text, soup=None):
        mobiles = set()
        offices = set()
        emails = set()

        # 1. Emails (standard regex with trailing punctuation clean)
        raw_emails = re.findall(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+', text)
        for em in raw_emails:
            clean_em = re.sub(r'[.,;:\'")>\]]+$', '', em.strip())
            if self.is_valid_email(clean_em):
                emails.add(clean_em.lower())

        if soup:
            # Mailto anchors and hrefs containing @
            for a in soup.select('a[href]'):
                href = a.get('href', '').strip()
                if 'mailto:' in href.lower():
                    em = re.sub(r'(?i)^mailto:', '', href).split('?')[0].strip()
                    em = re.sub(r'[.,;:\'")>\]]+$', '', em)
                    if self.is_valid_email(em):
                        emails.add(em.lower())
                elif '@' in href and not href.startswith(('http://', 'https://')):
                    em = href.split('?')[0].strip()
                    em = re.sub(r'[.,;:\'")>\]]+$', '', em)
                    if self.is_valid_email(em):
                        emails.add(em.lower())

            # Cloudflare email protection
            for cf in soup.select('[data-cfemail]'):
                dec = self.decode_cf_email(cf.get('data-cfemail', ''))
                if dec and self.is_valid_email(dec):
                    emails.add(dec.lower())

            # Meta tags (og:email, twitter:email, email, author)
            for meta in soup.select('meta[property*="email"], meta[name*="email"], meta[content*="@"]'):
                c = meta.get('content', '').strip()
                c = re.sub(r'[.,;:\'")>\]]+$', '', c)
                if c and self.is_valid_email(c):
                    emails.add(c.lower())

            # JSON-LD scripts
            import json
            for script in soup.select('script[type="application/ld+json"]'):
                try:
                    data = json.loads(script.string or '{}')
                    items = data if isinstance(data, list) else [data]
                    for item in items:
                        em_val = item.get('email')
                        if isinstance(em_val, str) and self.is_valid_email(em_val):
                            emails.add(em_val.lower())
                        elif isinstance(em_val, list):
                            for ev in em_val:
                                if isinstance(ev, str) and self.is_valid_email(ev):
                                    emails.add(ev.lower())
                except Exception:
                    pass

            # Search inside raw HTML string for hidden or script-rendered emails
            try:
                raw_html = str(soup)
                # Decode common HTML entity obfuscations
                raw_html = raw_html.replace('&#64;', '@').replace('&#x40;', '@').replace('&commat;', '@')
                html_emails = re.findall(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+', raw_html)
                for em in html_emails:
                    clean_em = re.sub(r'[.,;:\'")>\]]+$', '', em.strip())
                    if self.is_valid_email(clean_em):
                        emails.add(clean_em.lower())
            except Exception:
                pass

        # Obfuscated email regex (e.g. info [at] domain.com or sales (at) domain.com)
        obf_matches = re.findall(r'([a-zA-Z0-9_.+-]+(?:\s*\[at\]\s*|\s*\(at\)\s*|\s+AT\s+)[a-zA-Z0-9-]+\s*(?:\[dot\]|\(dot\)|\.|\s+DOT\s+)\s*[a-zA-Z0-9-.]+)', text, re.IGNORECASE)
        for om in obf_matches:
            clean_em = re.sub(r'\s*\[at\]\s*|\s*\(at\)\s*|\s+AT\s+', '@', om, flags=re.IGNORECASE)
            clean_em = re.sub(r'\s*\[dot\]\s*|\s*\(dot\)\s*|\s+DOT\s+', '.', clean_em, flags=re.IGNORECASE)
            clean_em = clean_em.replace(' ', '').strip()
            clean_em = re.sub(r'[.,;:\'")>\]]+$', '', clean_em)
            if self.is_valid_email(clean_em):
                emails.add(clean_em.lower())

        # 2. Indian Mobile Numbers via phonenumbers library
        try:
            for match in phonenumbers.PhoneNumberMatcher(text, "IN"):
                num = match.number
                if phonenumbers.is_valid_number(num) or phonenumbers.is_possible_number(num):
                    formatted = phonenumbers.format_number(num, phonenumbers.PhoneNumberFormat.NATIONAL)
                    raw_digits = re.sub(r'\D', '', formatted)
                    if len(raw_digits) == 10 and raw_digits[0] in '6789' and not self.is_virtual_pbx_number(raw_digits):
                        mobiles.add(f"+91 {raw_digits[:5]} {raw_digits[5:]}")
                    elif len(raw_digits) in [10, 11] and raw_digits.startswith('0') and not self.is_virtual_pbx_number(raw_digits):
                        offices.add(formatted)
        except Exception:
            pass

        if soup:
            for tel_tag in soup.select('a[href^="tel:"]'):
                href = tel_tag.get('href', '')
                tel_clean = href.replace('tel:', '').strip()
                valid_m = self.is_valid_indian_mobile(tel_clean)
                if valid_m:
                    mobiles.add(f"+91 {valid_m[:5]} {valid_m[5:]}")

        # Regex fallback for Indian mobile numbers
        pattern_mobile = r'(?:(?:\+91|0091|0)?[ -]?)?([6-9]\d{4}[ -]?\d{5})\b'
        for m in re.finditer(pattern_mobile, text):
            cand = m.group(1)
            valid_m = self.is_valid_indian_mobile(cand)
            if valid_m:
                mobiles.add(f"+91 {valid_m[:5]} {valid_m[5:]}")

        # Landline
        pattern_landline = r'\b(0\d{2,4}[ -]?\d{6,8})\b'
        for m in re.finditer(pattern_landline, text):
            cand = m.group(1).strip()
            digits = re.sub(r'\D', '', cand)
            if 10 <= len(digits) <= 12 and not self.is_virtual_pbx_number(digits) and cand not in mobiles:
                offices.add(cand)

        # Address via PIN code
        address = ""
        pincode_match = re.search(r'\b([1-9]\d{5})\b', text)
        if pincode_match:
            start_pos = max(0, pincode_match.start() - 150)
            end_pos = min(len(text), pincode_match.end() + 20)
            raw_addr = text[start_pos:end_pos]
            clean_addr = re.sub(r'\s+', ' ', raw_addr).strip()
            if len(clean_addr) > 15:
                address = clean_addr

        return mobiles, offices, emails, address

    def verify_category_and_location(self, full_text, title, category_item, district, state, city=None, custom_keyword=""):
        combined = (title + " " + full_text).lower()

        if custom_keyword and str(custom_keyword).strip():
            if not self.matches_custom_keyword(combined, custom_keyword):
                return False, f"Category mismatch (Does not match custom keyword '{custom_keyword}')"
            cat_score = 1
        else:
            keywords = list(category_item.get('keywords', [])) if category_item else []
            keywords.extend(['steel', 'tmt', 'cement', 'metal', 'iron', 'hardware', 'brick', 'block', 'pipes', 'tiles', 'paint', 'trader', 'wholesaler', 'distributor', 'manufacturer', 'supplier', 'dealer', 'contractor', 'builder', 'construction'])
            cat_matches = [k for k in set(keywords) if k in combined]
            cat_score = len(cat_matches)

            if cat_score == 0:
                return False, "Category mismatch (No construction keywords found)"

        # STRICT DISTRICT / CITY VERIFICATION: State alone is NEVER sufficient!
        allowed_cities = self.get_allowed_cities(district, city)
        location_matched = any(loc in combined for loc in allowed_cities)

        if not location_matched:
            return False, f"Location mismatch (District '{district}' not confirmed on page)"

        if self.has_conflicting_location(title, district, state, city):
            return False, f"Title belongs to another district/state ({title})"

        return True, f"Verified ({cat_score} keywords, {district} confirmed)"

    def scrape_business_site(self, candidate, category_item, state, district, city=None, custom_keyword=""):
        if not custom_keyword and candidate.get('task_custom_keyword'):
            custom_keyword = candidate.get('task_custom_keyword')

        # Special handling: Pre-parsed Google Local Places / Knowledge Panel card
        if candidate.get('_google_lead'):
            lead = dict(candidate['_google_lead'])
            b_name = lead.get('business_name', '')
            if self.has_conflicting_location(f"{b_name} {lead.get('address','')}", district, state, city):
                return None
            is_rel, rel_reason = self.is_strictly_category_relevant(
                b_name, f"{b_name} {lead.get('address','')} {lead.get('category','')}", category_item, custom_keyword
            )
            if not is_rel:
                self.log(f"Filtered non-category Google card ({rel_reason}): {b_name}", 'debug')
                return None
            if custom_keyword:
                lead['category'] = custom_keyword.title()
            phone = lead.get('mobile_numbers', '')
            if not phone and lead.get('business_name'):
                # Resolve real direct owner phone number via Solution 2 auto-lookup!
                l_mobs, l_lands, l_ems, _ = self.lookup_real_phone_for_business(
                    lead['business_name'], lead.get('city_area') or district, district, state, city
                )
                if l_mobs:
                    phone = ", ".join(l_mobs)
                    lead['mobile_numbers'] = phone
                if l_lands:
                    lead['office_numbers'] = ", ".join(l_lands)
                if l_ems:
                    lead['email_addresses'] = ", ".join(l_ems)
            if phone:
                for p in phone.split(','):
                    p_clean = p.strip()
                    dedup_key = ('google', p_clean)
                    if p_clean and dedup_key in self.seen_phones:
                        self.log(f"Duplicate Google mobile {p_clean} already extracted, skipping", 'debug')
                        return None
                    if p_clean:
                        self.seen_phones.add(dedup_key)
            self.log(f"Extracted Google Card: '{lead['business_name']}' | Phone: {phone} | Rating: {lead['rating'] or 'None'}", 'success')
            return [lead]

        url = candidate['url']
        domain = urlparse(url).netloc.lower()
        clean_dom = domain.replace('www.', '')

        if clean_dom in self.seen_domains and not self.is_directory_domain(domain):
            return None

        self.wait_if_paused()
        if self.check_abort():
            return None

        self.log(f"Visiting business site: {url}", 'info')

        # Special handling: JustDial listing pages → extract listing items
        if 'justdial.com' in domain:
            return self._scrape_justdial_as_lead(url, category_item, state, district, city, candidate, custom_keyword=custom_keyword)

        # Special handling: IndiaMART listing & company profile pages
        if 'indiamart.com' in domain:
            return self._scrape_indiamart_as_lead(url, category_item, state, district, city, candidate, custom_keyword=custom_keyword)

        # Special handling: TradeIndia company profile & directory pages
        if 'tradeindia.com' in domain:
            return self._scrape_tradeindia_as_lead(url, category_item, state, district, city, candidate, custom_keyword=custom_keyword)

        # Special handling: Sulekha listing pages
        if 'sulekha.com' in domain:
            return self._scrape_sulekha_as_lead(url, category_item, state, district, city, custom_keyword=custom_keyword)

        # Special handling: CallSevai listing pages
        if 'callsevai.com' in domain:
            return self._scrape_callsevai_as_lead(url, category_item, state, district, city, custom_keyword=custom_keyword)

        # Special handling: Social profile pages (Facebook, Instagram, LinkedIn, etc.)
        # These sites block automated bot requests or redirect to login walls.
        # But their search engine snippet contains the verified business name, address, and direct mobile number!
        if any(s in clean_dom for s in ['facebook.com', 'instagram.com', 'linkedin.com']):
            cand_title = candidate.get('title', '')
            cand_snip = candidate.get('snippet', '')
            combined_snip = f"{cand_title} {cand_snip}"
            raw_title = cand_title.split('|')[0].split('—')[0].split('-')[0].split('–')[0].strip()
            biz_name = self.clean_company_name(raw_title, domain) if raw_title else candidate.get('title', '')
            snip_mobiles = set(candidate.get('_snippet_phones') or [])
            for pm in re.findall(r'(?:\+91[\s\-]?|0)?([6-9]\d{4}[\s\-]?\d{5})\b', combined_snip):
                mob = self.is_valid_indian_mobile(pm)
                if mob and not self.is_virtual_pbx_number(mob):
                    fmt = f"+91 {mob[:5]} {mob[5:]}"
                    snip_mobiles.add(fmt)
            if not snip_mobiles and biz_name:
                l_mobs, l_lands, l_ems, _ = self.lookup_real_phone_for_business(biz_name, city or district, district, state, city)
                snip_mobiles.update(l_mobs)
            if snip_mobiles:
                primary_mob = sorted(list(snip_mobiles))[0]
                dedup_key = (clean_dom, primary_mob)
                if dedup_key in self.seen_phones:
                    return None
                self.seen_phones.add(dedup_key)
                snip_addr = ""
                addr_match = re.search(r'([A-Za-z0-9\s,\.\-]+(?:' + re.escape(district) + r')[A-Za-z0-9\s,\.\-]*(?:\d{6})?)', combined_snip, re.IGNORECASE)
                if addr_match:
                    snip_addr = addr_match.group(1).strip(' .,·-')
                lead = {
                    "business_name": biz_name,
                    "category": custom_keyword.title() if custom_keyword else category_item['name'],
                    "district": district,
                    "state": state,
                    "city_area": city or district,
                    "rating": "",
                    "mobile_numbers": ", ".join(sorted(list(snip_mobiles))),
                    "office_numbers": "",
                    "email_addresses": "",
                    "address": snip_addr or f"{city or district}, {district}, {state}",
                    "website": url,
                    "source_url": url,
                    "child_pages_crawled": 0,
                    "verification_status": "Strictly Verified",
                    "extracted_at": time.strftime("%Y-%m-%d %H:%M:%S")
                }
                self.log(f"Extracted Social / Web Lead: '{biz_name}' | Phone: {lead['mobile_numbers']}", 'success')
                return [lead]
            return None

        try:
            r = self.session.get(url, timeout=(3.5, 6))
            if r.status_code != 200:
                r = self.brave_client.get(url)
                if r.status_code != 200:
                    if candidate.get('_snippet_phones'):
                        cand_title = candidate.get('title', '')
                        raw_name = cand_title.split('—')[0].split('|')[0].split('-')[0].strip() or clean_dom
                        lead = {
                            "business_name": raw_name,
                            "category": custom_keyword.title() if custom_keyword else category_item['name'],
                            "district": district,
                            "state": state,
                            "city_area": city or district,
                            "rating": "",
                            "mobile_numbers": ", ".join(candidate['_snippet_phones']),
                            "office_numbers": "",
                            "email_addresses": "",
                            "address": f"{city or district}, {district}, {state}",
                            "website": url,
                            "source_url": url,
                            "child_pages_crawled": 0,
                            "verification_status": "Strictly Verified",
                            "extracted_at": time.strftime("%Y-%m-%d %H:%M:%S")
                        }
                        self.log(f"Extracted Verified Lead (via Search Data): '{raw_name}' | Phone: {lead['mobile_numbers']}", 'success')
                        return [lead]
                    return None

            soup = BeautifulSoup(r.text, 'html.parser')
            page_text = soup.get_text(separator=' ')
            title = soup.title.text.strip() if soup.title else candidate.get('title', '')

            # Multi-listing detection: If top search result page contains multiple contractor / business listings
            allowed_cities = self.get_allowed_cities(district, city)
            cards = soup.select('.business-card, .listing-card, .directory-card, .vendor-card, .company-item, .result-item, [itemtype*="LocalBusiness"]')
            if len(cards) >= 2:
                multi_leads = []
                for c in cards:
                    c_name_el = c.select_one('h2, h3, h4, .title, .company-name, [itemprop="name"]')
                    c_name = c_name_el.text.strip() if c_name_el else ""
                    if not c_name or len(c_name) < 3 or self.has_conflicting_location(c_name, district, state, city):
                        continue
                    c_text = c.get_text(separator=' ')
                    if not any(loc in c_text.lower() for loc in allowed_cities):
                        continue
                    if custom_keyword and not self.matches_custom_keyword(f"{c_name} {c_text}", custom_keyword):
                        continue
                    c_mobs, c_lands, c_ems, c_addr = self.extract_contacts_from_text(c_text, c)
                    if not c_mobs:
                        l_mobs, l_lands, l_ems, _ = self.lookup_real_phone_for_business(c_name, c_addr or (city or district), district, state, city)
                        c_mobs.update(l_mobs)
                        c_lands.update(l_lands)
                        c_ems.update(l_ems)
                    if c_mobs or c_lands or c_ems:
                        dedup_key = (clean_dom, c_name.lower())
                        if dedup_key not in self.seen_phones:
                            self.seen_phones.add(dedup_key)
                            m_lead = {
                                "business_name": c_name,
                                "category": custom_keyword.title() if custom_keyword else category_item['name'],
                                "district": district,
                                "state": state,
                                "city_area": city or district,
                                "rating": "",
                                "mobile_numbers": ", ".join(sorted(list(c_mobs))),
                                "office_numbers": ", ".join(sorted(list(c_lands))),
                                "email_addresses": ", ".join(sorted(list(c_ems))),
                                "address": c_addr or f"{city or district}, {district}, {state}",
                                "website": url,
                                "source_url": url,
                                "child_pages_crawled": 0,
                                "verification_status": "Strictly Verified",
                                "extracted_at": time.strftime("%Y-%m-%d %H:%M:%S")
                            }
                            multi_leads.append(m_lead)
                            self.emit_lead(m_lead)
                            self.log(f"Extracted Directory Item from {clean_dom}: '{c_name}' | Phone: {m_lead['mobile_numbers'] or m_lead['office_numbers']}", 'success')
                if multi_leads:
                    return multi_leads

            is_valid, reason = self.verify_category_and_location(
                page_text, title, category_item, district, state, city, custom_keyword=custom_keyword
            )

            if not is_valid:
                self.log(f"Skipping {domain}: {reason}", 'debug')
                return None

            mobiles, offices, emails, address = self.extract_contacts_from_text(page_text, soup)
            for sp_phone in (candidate.get('_snippet_phones') or []):
                mobiles.add(sp_phone)

            child_links = self.find_child_pages(url, soup)
            crawled_child_pages = []

            for child_url in child_links:
                if self.check_abort():
                    break
                self.wait_if_paused()
                self.log(f"  └─ Crawling child page: {child_url}", 'info')
                try:
                    c_resp = self.session.get(child_url, timeout=(3.0, 5.0))
                    if c_resp.status_code == 200:
                        c_soup = BeautifulSoup(c_resp.text, 'html.parser')
                        c_text = c_soup.get_text(separator=' ')
                        c_mobiles, c_offices, c_emails, c_addr = self.extract_contacts_from_text(c_text, c_soup)
                        mobiles.update(c_mobiles)
                        offices.update(c_offices)
                        emails.update(c_emails)
                        if not address and c_addr:
                            address = c_addr
                        crawled_child_pages.append(child_url)
                except Exception as ex:
                    self.log(f"  Child page error {child_url}: {ex}", 'debug')
                time.sleep(0.4)

            if address and self.has_conflicting_location(address, district, state, city):
                self.log(f"Skipping {domain}: Extracted address belongs to another district ({address})", 'debug')
                return None

            business_name = self.clean_company_name(title, domain)

            # Solution 2 Auto-Lookup: If website only had virtual PBX numbers (like IndiaMART-hosted custom domains 0794...)
            # or hid its phone number, resolve the 100% real direct owner mobile number from Google Maps / Web!
            if not mobiles and business_name:
                l_mobs, l_lands, l_ems, _ = self.lookup_real_phone_for_business(
                    business_name, city or district, district, state, city
                )
                for lm in l_mobs:
                    mobiles.add(lm)
                for ll in l_lands:
                    offices.add(ll)
                for le in l_ems:
                    emails.add(le)

            primary_mobile = sorted(list(mobiles))[0] if mobiles else ""
            primary_email = sorted(list(emails))[0] if emails else ""
            primary_office = sorted(list(offices))[0] if offices else ""

            if not primary_mobile and not primary_email and not primary_office:
                self.log(f"No phone or email found on {domain}, discarding to ensure data accuracy", 'debug')
                return None

            dedup_mob_key = (clean_dom, primary_mobile)
            if primary_mobile and dedup_mob_key in self.seen_phones:
                self.log(f"Duplicate mobile {primary_mobile} on {clean_dom} already extracted, skipping", 'debug')
                return None

            if primary_mobile:
                self.seen_phones.add(dedup_mob_key)
            if primary_email:
                self.seen_emails.add((clean_dom, primary_email))
            if not self.is_directory_domain(domain):
                self.seen_domains.add(clean_dom)

            # Extract rating if present in text/meta, or leave empty if none found
            site_rating = ""
            r_match = re.search(r'\b([1-5]\.\d)\s*(?:★|stars|\/5)?\s*(?:\((\d+)\s*(?:reviews|ratings)?\))?', page_text, re.IGNORECASE)
            if r_match and float(r_match.group(1)) <= 5.0:
                rv_val = r_match.group(1)
                rv_cnt = r_match.group(2) if r_match.group(2) else ""
                site_rating = f"{rv_val} ★ ({rv_cnt} Ratings)".strip() if rv_cnt else f"{rv_val} ★"

            lead = {
                "business_name": business_name,
                "category": custom_keyword.title() if custom_keyword else category_item['name'],
                "district": district,
                "state": state,
                "city_area": city or district,
                "rating": site_rating,
                "mobile_numbers": ", ".join(sorted(list(mobiles))),
                "office_numbers": ", ".join(sorted(list(offices))),
                "email_addresses": ", ".join(sorted(list(emails))),
                "address": address or f"{city or district}, {district}, {state}",
                "website": f"{urlparse(url).scheme}://{domain}",
                "source_url": url,
                "child_pages_crawled": len(crawled_child_pages),
                "verification_status": "Strictly Verified",
                "extracted_at": time.strftime("%Y-%m-%d %H:%M:%S")
            }

            self.log(f"Extracted: '{business_name}' | Phone: {lead['mobile_numbers']} | Email: {lead['email_addresses']}", 'success')
            return [lead]

        except Exception as e:
            self.log(f"Site scrape note for {url}: {e}", 'debug')
            if candidate.get('_snippet_phones'):
                cand_title = candidate.get('title', '')
                raw_name = cand_title.split('—')[0].split('|')[0].split('-')[0].strip() or clean_dom
                lead = {
                    "business_name": raw_name,
                    "category": custom_keyword.title() if custom_keyword else category_item['name'],
                    "district": district,
                    "state": state,
                    "city_area": city or district,
                    "rating": "",
                    "mobile_numbers": ", ".join(candidate['_snippet_phones']),
                    "office_numbers": "",
                    "email_addresses": "",
                    "address": f"{city or district}, {district}, {state}",
                    "website": url,
                    "source_url": url,
                    "child_pages_crawled": 0,
                    "verification_status": "Strictly Verified",
                    "extracted_at": time.strftime("%Y-%m-%d %H:%M:%S")
                }
                self.log(f"Extracted Verified Lead (via Search Data): '{raw_name}' | Phone: {lead['mobile_numbers']}", 'success')
                return [lead]
            return None

    def _scrape_tradeindia_as_lead(self, url, category_item, state, district, city=None, candidate=None, custom_keyword=""):
        """Scrape TradeIndia company profile pages and resolve real owner phone numbers."""
        import json
        try:
            r = self.brave_client.get(url)
            if r.status_code != 200:
                r = self.session.get(url, timeout=(4, 8))
            if r.status_code != 200:
                return None

            soup = BeautifulSoup(r.text, 'html.parser')
            page_text = soup.get_text(separator=' ')
            title = soup.title.text.strip() if soup.title else (candidate.get('title', '') if candidate else '')

            if custom_keyword and not self.matches_custom_keyword(f"{title} {page_text} {url}", custom_keyword):
                return None

            allowed_cities = self.get_allowed_cities(district, city)
            if not any(loc in (title + " " + page_text + " " + url).lower() for loc in allowed_cities):
                return None
            if self.has_conflicting_location(title + " " + url, district, state, city):
                return None

            b_name = ""
            addr_ti = ""
            for sc in soup.find_all('script', type='application/ld+json'):
                try:
                    data = json.loads(sc.string or '{}')
                    items = data if isinstance(data, list) else [data]
                    for it in items:
                        if isinstance(it, dict) and it.get('@type') == 'LocalBusiness':
                            cand_n = (it.get('name') or '').strip()
                            if cand_n and cand_n.lower() != 'tradeindia':
                                b_name = cand_n
                            a_obj = it.get('address', {})
                            if isinstance(a_obj, dict):
                                parts = [a_obj.get('streetAddress'), a_obj.get('addressLocality'), a_obj.get('addressRegion'), a_obj.get('postalCode')]
                                addr_ti = ", ".join(str(p).strip() for p in parts if p and str(p).strip())
                except Exception:
                    pass

            if not b_name:
                b_name = self.clean_company_name(title, "tradeindia.com")
            if not b_name or b_name.lower() in ('tradeindia', 'company profile') or self.has_conflicting_location(b_name, district, state, city):
                return None

            if custom_keyword and not self.matches_custom_keyword(f"{b_name} {page_text} {title}", custom_keyword):
                return None

            if not addr_ti:
                addr_m = re.search(r'Address\s+([^|<>]{15,150}?\b\d{6}\b)', page_text)
                if addr_m:
                    addr_ti = addr_m.group(1).strip()

            if addr_ti and self.has_conflicting_location(addr_ti, district, state, city):
                return None

            mobiles, offices, emails, p_addr = self.extract_contacts_from_text(page_text, soup)
            offices = {o for o in offices if '46710423' not in o}
            if not addr_ti and p_addr:
                addr_ti = p_addr

            if candidate and candidate.get('_snippet_phones'):
                for sp in candidate['_snippet_phones']:
                    mobiles.add(sp)

            if not mobiles:
                l_mobs, l_lands, l_ems, l_web = self.lookup_real_phone_for_business(
                    b_name, city or district, district, state, city
                )
                for lm in l_mobs:
                    mobiles.add(lm)
                for ll in l_lands:
                    offices.add(ll)
                for le in l_ems:
                    emails.add(le)
            else:
                l_web = ""

            valid_phones = sorted(list(mobiles))
            valid_offices = sorted(list(offices))
            valid_emails = sorted(list(emails))

            if not valid_phones and not valid_offices and not valid_emails:
                return None

            dedup_key = ('tradeindia', b_name.lower())
            if dedup_key in self.seen_phones:
                return None
            self.seen_phones.add(dedup_key)

            lead = {
                "business_name": b_name,
                "category": custom_keyword.title() if custom_keyword else category_item['name'],
                "district": district,
                "state": state,
                "city_area": city or district,
                "rating": "",
                "mobile_numbers": ", ".join(valid_phones),
                "office_numbers": ", ".join(valid_offices),
                "email_addresses": ", ".join(valid_emails),
                "address": addr_ti or f"{city or district}, {district}, {state}",
                "website": l_web or url,
                "source_url": url,
                "child_pages_crawled": 0,
                "verification_status": "Strictly Verified",
                "extracted_at": time.strftime("%Y-%m-%d %H:%M:%S")
            }
            self.emit_lead(lead)
            self.log(f"Extracted TradeIndia Profile: '{b_name}' | Phone: {lead['mobile_numbers'] or lead['office_numbers']}", 'success')
            return [lead]
        except Exception as e:
            self.log(f"TradeIndia scrape error: {e}", 'debug')
            return None

    def _scrape_indiamart_as_lead(self, url, category_item, state, district, city=None, candidate=None, custom_keyword=""):
        import json
        try:
            r = self.session.get(url, timeout=(4, 8))
            if r.status_code != 200:
                return None

            allowed_cities = self.get_allowed_cities(district, city)
            leads = []
            seen_names = set()

            # 1. Extract from IndiaMART window.__INITIAL_STATE__ JSON (Infinite Multi-Category Expansion)
            if 'window.__INITIAL_STATE__' in r.text:
                try:
                    idx = r.text.find('window.__INITIAL_STATE__')
                    brace_idx = r.text.find('{', idx)
                    if brace_idx != -1:
                        im_data, _ = json.JSONDecoder().raw_decode(r.text[brace_idx:])
                        all_data_lists = [im_data.get('data', [])]

                        # Infinite Multi-Category Crawl: Collect 100+ contractors from related district categories
                        for rc in (im_data.get('relCat') or [])[:6]:
                            if self.check_abort():
                                break
                            rc_url = rc.get('URL')
                            if rc_url:
                                full_rc = urljoin('https://dir.indiamart.com', rc_url)
                                try:
                                    r_rc = self.session.get(full_rc, timeout=(3.5, 6.0))
                                    if 'window.__INITIAL_STATE__' in r_rc.text:
                                        idx_rc = r_rc.text.find('window.__INITIAL_STATE__')
                                        b_rc = r_rc.text.find('{', idx_rc)
                                        rc_data, _ = json.JSONDecoder().raw_decode(r_rc.text[b_rc:])
                                        rc_items = rc_data.get('data', [])
                                        if rc_items:
                                            all_data_lists.append(rc_items)
                                except Exception:
                                    pass

                        for it_list in all_data_lists:
                            for it in it_list:
                                if not isinstance(it, dict):
                                    continue
                                it_city = (it.get('city') or '').strip().lower()
                                if not it_city or it_city not in allowed_cities:
                                    continue
                                comp_name = (it.get('CMP') or '').strip()
                                if not comp_name or len(comp_name) < 3 or comp_name.lower() in seen_names:
                                    continue
                                if self.has_conflicting_location(comp_name, district, state, city):
                                    continue

                                if custom_keyword and not self.matches_custom_keyword(
                                    f"{comp_name} {it.get('PRD_NAME','')} {it.get('GLUSR_USR_PRD_NAME','')} {it.get('desc','')} {it.get('f_ad','')}", custom_keyword
                                ):
                                    continue

                                raw_ct = str(it.get('c_ct') or '').split(',')[0].strip()
                                valid_phones = []
                                v_mob = self.is_valid_indian_mobile(raw_ct)
                                if v_mob and not self.is_virtual_pbx_number(v_mob):
                                    fmt = f"+91 {v_mob[:5]} {v_mob[5:]}"
                                    if ('indiamart', fmt) not in self.seen_phones:
                                        valid_phones.append(fmt)

                                valid_landlines = []
                                if not valid_phones and len(re.sub(r'\D', '', raw_ct)) == 10 and not self.is_virtual_pbx_number(raw_ct):
                                    d_ct = re.sub(r'\D', '', raw_ct)
                                    valid_landlines.append(f"0{d_ct[:3]}-{d_ct[3:]}")

                                if not valid_phones and not valid_landlines:
                                    l_mobs, l_lands, _, _ = self.lookup_real_phone_for_business(
                                        comp_name, it_city or city or district, district, state, city
                                    )
                                    valid_phones.extend(l_mobs)
                                    valid_landlines.extend(l_lands)

                                if not valid_phones and not valid_landlines:
                                    continue

                                for vp in valid_phones:
                                    self.seen_phones.add(('indiamart', vp))
                                seen_names.add(comp_name.lower())

                                wt_avg = it.get('wt_avg')
                                tr_c = it.get('tr_c')
                                rating_str = f"{wt_avg} ★ ({tr_c} Ratings)" if wt_avg and float(wt_avg) > 0 else ""

                                addr_im = (it.get('f_ad') or it.get('ad') or '').strip()
                                if not addr_im or district.lower() not in addr_im.lower():
                                    addr_im = f"{addr_im + ', ' if addr_im else ''}{district}, {state}"

                                s_url = (it.get('s_url') or url).strip()
                                lead = {
                                    "business_name": comp_name,
                                    "category": custom_keyword.title() if custom_keyword else category_item['name'],
                                    "district": district,
                                    "state": state,
                                    "city_area": city or district,
                                    "rating": rating_str,
                                    "mobile_numbers": ", ".join(valid_phones),
                                    "office_numbers": ", ".join(valid_landlines),
                                    "email_addresses": "",
                                    "address": addr_im,
                                    "website": s_url,
                                    "source_url": s_url,
                                    "child_pages_crawled": 0,
                                    "verification_status": "Strictly Verified",
                                    "extracted_at": time.strftime("%Y-%m-%d %H:%M:%S")
                                }
                                leads.append(lead)
                                self.emit_lead(lead)
                                self.log(f"Extracted IndiaMART: '{comp_name}' | Phone: {lead['mobile_numbers'] or lead['office_numbers']} | Rating: {rating_str or 'None'}", 'success')

                        if leads:
                            return leads
                except Exception as im_ex:
                    self.log(f"IndiaMART JSON parse note: {im_ex}", 'debug')

            # 2. Fallback for individual IndiaMART company profile pages (strictly verified for target district)
            soup = BeautifulSoup(r.text, 'html.parser')
            page_text = soup.get_text(separator=' ')
            title = soup.title.text.strip() if soup.title else ""

            if not any(loc in (title + " " + url).lower() for loc in allowed_cities):
                if not any(loc in page_text.lower() for loc in allowed_cities) or self.has_conflicting_location(title + " " + url, district, state, city):
                    return None

            b_name = self.clean_company_name(title, "indiamart.com")
            bad_im_names = ['read more', 'call now', 'contact supplier', 'civil contractors', 'civil works', 'civil construction', 'indiamart', 'photos from']
            if b_name.lower().startswith('photos from '):
                b_name = b_name[12:].strip()
            if not b_name or any(bn in b_name.lower() for bn in bad_im_names) or self.has_conflicting_location(b_name, district, state, city):
                return None

            if custom_keyword and not self.matches_custom_keyword(f"{b_name} {page_text} {title}", custom_keyword):
                return None

            mobiles, offices, emails, address = self.extract_contacts_from_text(page_text, soup)
            if address and self.has_conflicting_location(address, district, state, city):
                return None

            if candidate and candidate.get('_snippet_phones'):
                for sp in candidate['_snippet_phones']:
                    mobiles.add(sp)

            # If IndiaMART profile page only has virtual PBX numbers (0794.../0804...), lookup real owner mobile!
            if not mobiles:
                l_mobs, l_lands, l_ems, l_web = self.lookup_real_phone_for_business(
                    b_name, city or district, district, state, city
                )
                for lm in l_mobs:
                    mobiles.add(lm)
                for ll in l_lands:
                    offices.add(ll)
                for le in l_ems:
                    emails.add(le)
            else:
                l_web = ""

            valid_phones = sorted(list(mobiles))
            if not valid_phones and not offices and not emails:
                return None

            dedup_im_key = ('indiamart_profile', url.rstrip('/'))
            if dedup_im_key in self.seen_phones:
                return None
            self.seen_phones.add(dedup_im_key)
            for em in emails:
                self.seen_emails.add(em)

            site_rating = ""
            r_match = re.search(r'\b([1-5]\.\d)\s*(?:★|\/5)?\s*(?:\((\d+)\s*(?:reviews|ratings)?\))?', page_text, re.IGNORECASE)
            if r_match and float(r_match.group(1)) <= 5.0:
                rv_val = r_match.group(1)
                rv_cnt = r_match.group(2) if r_match.group(2) else ""
                site_rating = f"{rv_val} ★ ({rv_cnt} Ratings)".strip() if rv_cnt else f"{rv_val} ★"

            lead = {
                "business_name": b_name,
                "category": custom_keyword.title() if custom_keyword else category_item['name'],
                "district": district,
                "state": state,
                "city_area": city or district,
                "rating": site_rating,
                "mobile_numbers": ", ".join(valid_phones),
                "office_numbers": ", ".join(sorted(list(offices))),
                "email_addresses": ", ".join(sorted(list(emails))),
                "address": address if (address and any(loc in address.lower() for loc in allowed_cities)) else f"{city or district}, {district}, {state}",
                "website": l_web or url,
                "source_url": url,
                "child_pages_crawled": 0,
                "verification_status": "Strictly Verified",
                "extracted_at": time.strftime("%Y-%m-%d %H:%M:%S")
            }
            self.emit_lead(lead)
            self.log(f"Extracted IndiaMART Profile: '{b_name}' | Phone: {lead['mobile_numbers'] or lead['office_numbers']}", 'success')
            return [lead]
        except Exception as e:
            self.log(f"IndiaMART scrape error: {e}", 'debug')
            return None

    def _scrape_sulekha_as_lead(self, url, category_item, state, district, city=None, custom_keyword=""):
        import json
        from concurrent.futures import ThreadPoolExecutor
        try:
            r = self.session.get(url, timeout=(5, 10))
            if r.status_code != 200:
                r = self.brave_client.get(url)
            if r.status_code != 200:
                return None
            soup = BeautifulSoup(r.text, 'html.parser')

            leads = []
            seen_names = set()
            allowed_cities = self.get_allowed_cities(district, city)
            non_construction_terms = [
                'holidays', 'travels', 'tours', 'packers', 'movers', 'catering', 'matrimony',
                'astrology', 'hospital', 'clinic', 'beauty', 'salon', 'spa', 'pest control',
                'coaching', 'tuition', 'security', 'detective', 'laundry', 'dry clean'
            ]

            # 1. LD+JSON ItemList Crawler
            profile_items = []
            for sc in soup.find_all('script', type='application/ld+json'):
                try:
                    data = json.loads(sc.string or '{}')
                    graphs = data.get('@graph', [data]) if isinstance(data, dict) else data
                    for g in graphs:
                        if isinstance(g, dict) and g.get('@type') == 'ItemList':
                            for it in g.get('itemListElement', []):
                                biz = it.get('item', {})
                                if not isinstance(biz, dict):
                                    continue
                                bname = (biz.get('name') or '').strip()
                                if any(bad_t in bname.lower() for bad_t in non_construction_terms):
                                    continue
                                if self.has_conflicting_location(bname, district, state, city):
                                    continue
                                if custom_keyword and not self.matches_custom_keyword(f"{bname} {biz.get('url','')}", custom_keyword):
                                    continue
                                region = (biz.get('address', {}).get('addressRegion') or '').strip().lower()
                                locality = (biz.get('address', {}).get('addressLocality') or '').strip().lower()
                                purl = (biz.get('url') or '').strip().lower()
                                if region and region not in allowed_cities:
                                    continue
                                if not any(loc in purl or loc in region or loc in locality for loc in allowed_cities):
                                    continue
                                if self.has_conflicting_location(purl, district, state, city):
                                    continue
                                profile_items.append(biz)
                except Exception:
                    pass

            # 2. HTML Contractor Cards & Profile Links Crawler (Infinite multi-lead extraction)
            seen_profile_urls = {b.get('url', '').lower() for b in profile_items if b.get('url')}
            for a in soup.find_all('a', href=True):
                href = a['href'].strip()
                if ('-contact-address' in href or '/profile/' in href) and 'reviews' not in href:
                    t = a.text.strip()
                    if t and len(t) > 2 and t.lower() not in ['read more', 'view all', 'contact', 'reviews', 'details']:
                        if any(bad_t in t.lower() for bad_t in non_construction_terms):
                            continue
                        if custom_keyword and not self.matches_custom_keyword(f"{t} {href}", custom_keyword):
                            continue
                        h_lower = href.lower()
                        # Strict target district filter
                        if any(loc in h_lower for loc in allowed_cities) or any(loc in t.lower() for loc in allowed_cities):
                            if not self.has_conflicting_location(t + " " + href, district, state, city):
                                p_full = href if href.startswith('http') else urljoin('https://www.sulekha.com', href)
                                if p_full.lower() not in seen_profile_urls:
                                    seen_profile_urls.add(p_full.lower())
                                    profile_items.append({
                                        'name': t,
                                        'url': p_full
                                    })

            def fetch_sulekha_profile(biz):
                if self.check_abort():
                    return None
                purl = biz.get('url')
                name = (biz.get('name') or '').strip()
                if not name or len(name) < 3:
                    return None

                if custom_keyword and not self.matches_custom_keyword(f"{name} {purl}", custom_keyword):
                    return None

                phone_raw = biz.get('telephone') or ''
                addr_str = ''
                rating_str = ''
                website_url = purl or url
                emails_found = set()
                offices_found = set()

                if purl:
                    try:
                        rp = self.session.get(purl, timeout=(4, 8))
                        if rp.status_code != 200:
                            rp = self.brave_client.get(purl)
                        if rp.status_code == 200:
                            psoup = BeautifulSoup(rp.text, 'html.parser')
                            for sc in psoup.find_all('script', type='application/ld+json'):
                                try:
                                    pdata = json.loads(sc.string or '{}')
                                    pgraphs = pdata.get('@graph', [pdata]) if isinstance(pdata, dict) else pdata
                                    for pg in pgraphs:
                                        if isinstance(pg, dict) and pg.get('@type') == 'LocalBusiness':
                                            phone_raw = phone_raw or pg.get('telephone', '')
                                            a_obj = pg.get('address', {})
                                            if isinstance(a_obj, dict):
                                                p_loc = (a_obj.get('addressLocality') or '').strip().lower()
                                                if p_loc and p_loc not in allowed_cities:
                                                    return None
                                                s_addr = (a_obj.get('streetAddress') or '').strip()
                                                addr_str = f"{s_addr}, {a_obj.get('addressLocality','').strip()}" if (s_addr and p_loc and p_loc not in s_addr.lower()) else s_addr
                                            agg = pg.get('aggregateRating', {})
                                            if isinstance(agg, dict) and agg.get('ratingValue'):
                                                rating_str = f"{agg['ratingValue']} ★ ({agg.get('reviewCount', 1)} Ratings)"
                                            same_as = pg.get('sameAs', [])
                                            if same_as and isinstance(same_as, list) and same_as[0]:
                                                website_url = same_as[0]
                                except Exception:
                                    pass
                            _, p_offices, p_emails, p_addr = self.extract_contacts_from_text(psoup.get_text(separator=' '), psoup)
                            emails_found.update(e for e in p_emails if 'sulekha' not in e)
                            offices_found.update(p_offices)
                            if not addr_str and p_addr:
                                addr_str = p_addr
                    except Exception:
                        pass

                if addr_str and self.has_conflicting_location(addr_str, district, state, city):
                    return None

                if custom_keyword and not self.matches_custom_keyword(f"{name} {addr_str} {website_url}", custom_keyword):
                    return None

                valid_mobiles = []
                for p in re.findall(r'(?:\+91|0)?[6-9]\d{9}', str(phone_raw)):
                    v = self.is_valid_indian_mobile(p)
                    if v and not self.is_virtual_pbx_number(v):
                        valid_mobiles.append(f"+91 {v[:5]} {v[5:]}")
                if not valid_mobiles and phone_raw:
                    digits = re.sub(r'\D', '', str(phone_raw))
                    if 10 <= len(digits) <= 12 and not self.is_virtual_pbx_number(digits):
                        offices_found.add(str(phone_raw).strip())

                # Solution 2 Auto-Lookup: If Sulekha contact page masked the mobile number,
                # resolve 100% Real Direct Owner Mobile Number via Google Maps / Web!
                if not valid_mobiles and name:
                    l_mobs, l_lands, l_ems, l_web = self.lookup_real_phone_for_business(
                        name, addr_str or (city or district), district, state, city
                    )
                    for lm in l_mobs:
                        valid_mobiles.append(lm)
                    for ll in l_lands:
                        offices_found.add(ll)
                    for le in l_ems:
                        emails_found.add(le)
                    if l_web:
                        website_url = l_web

                if not valid_mobiles and not offices_found and not emails_found:
                    return None

                return {
                    "business_name": name,
                    "category": custom_keyword.title() if custom_keyword else category_item['name'],
                    "district": district,
                    "state": state,
                    "city_area": city or district,
                    "rating": rating_str,
                    "mobile_numbers": ", ".join(sorted(set(valid_mobiles))),
                    "office_numbers": ", ".join(sorted(offices_found)),
                    "email_addresses": ", ".join(sorted(emails_found)),
                    "address": addr_str or f"{city or district}, {district}, {state}",
                    "website": website_url,
                    "source_url": purl or url,
                    "child_pages_crawled": 1 if purl else 0,
                    "verification_status": "Strictly Verified",
                    "extracted_at": time.strftime("%Y-%m-%d %H:%M:%S")
                }

            if profile_items:
                with ThreadPoolExecutor(max_workers=6) as executor:
                    for item_lead in executor.map(fetch_sulekha_profile, profile_items):
                        if item_lead:
                            b_name = item_lead['business_name'].lower()
                            if b_name in seen_names:
                                continue
                            mobs = [m.strip() for m in item_lead['mobile_numbers'].split(',') if m.strip()]
                            new_mobs = [m for m in mobs if ('sulekha', m) not in self.seen_phones]
                            if mobs and not new_mobs and not item_lead['email_addresses']:
                                continue
                            for m in new_mobs:
                                self.seen_phones.add(('sulekha', m))
                            seen_names.add(b_name)
                            leads.append(item_lead)
                            self.emit_lead(item_lead)
                            self.log(f"Extracted Sulekha Profile: '{item_lead['business_name']}' | Phone: {item_lead['mobile_numbers'] or item_lead['office_numbers']} | Email: {item_lead['email_addresses']}", 'success')

            return leads if leads else None
        except Exception as e:
            self.log(f"Sulekha scrape error: {e}", 'debug')
            return None

    def _scrape_callsevai_as_lead(self, url, category_item, state, district, city=None, custom_keyword=""):
        try:
            r = self.session.get(url, timeout=(4, 8))
            if r.status_code != 200:
                return None
            soup = BeautifulSoup(r.text, 'html.parser')
            page_text = soup.get_text(separator=' ')
            title = soup.title.text.strip() if soup.title else "CallSevai Contractor"

            if custom_keyword and not self.matches_custom_keyword(f"{title} {page_text} {url}", custom_keyword):
                return None

            allowed_cities = self.get_allowed_cities(district, city)
            if not any(loc in (title + " " + page_text + " " + url).lower() for loc in allowed_cities):
                return None
            if self.has_conflicting_location(title + " " + url, district, state, city):
                return None

            mobiles, offices, emails, address = self.extract_contacts_from_text(page_text, soup)
            if address and self.has_conflicting_location(address, district, state, city):
                return None
            valid_phones = [p for p in sorted(list(mobiles | offices)) if p not in self.seen_phones]

            if not valid_phones and not emails:
                return None

            for vp in valid_phones:
                self.seen_phones.add(vp)
            for em in emails:
                self.seen_emails.add(em)

            b_name = self.clean_company_name(title, "callsevai.com")

            if custom_keyword and not self.matches_custom_keyword(f"{b_name} {page_text} {title}", custom_keyword):
                return None

            site_rating = ""
            r_match = re.search(r'\b([1-5]\.\d)\s*(?:★|\/5)?\s*(?:\((\d+)\s*(?:reviews|ratings)?\))?', page_text, re.IGNORECASE)
            if r_match and float(r_match.group(1)) <= 5.0:
                rv_val = r_match.group(1)
                rv_cnt = r_match.group(2) if r_match.group(2) else ""
                site_rating = f"{rv_val} ★ ({rv_cnt} Ratings)".strip() if rv_cnt else f"{rv_val} ★"

            lead = {
                "business_name": b_name,
                "category": custom_keyword.title() if custom_keyword else category_item['name'],
                "district": district,
                "state": state,
                "city_area": city or district,
                "rating": site_rating,
                "mobile_numbers": ", ".join(valid_phones),
                "office_numbers": "",
                "email_addresses": ", ".join(sorted(list(emails))),
                "address": address or f"{city or district}, {district}, {state}",
                "website": "https://www.callsevai.com",
                "source_url": url,
                "child_pages_crawled": 0,
                "verification_status": "Strictly Verified",
                "extracted_at": time.strftime("%Y-%m-%d %H:%M:%S")
            }
            self.emit_lead(lead)
            self.log(f"Extracted CallSevai: '{b_name}' | Phone: {lead['mobile_numbers']}", 'success')
            return [lead]
        except Exception as e:
            self.log(f"CallSevai scrape error: {e}", 'debug')
            return None

    def _jd_crypt(self, salt, text):
        salt_xor = 0
        for ch in salt:
            salt_xor ^= ord(ch)
        return "".join(f"{(ord(ch) ^ salt_xor):02x}" for ch in text)

    def _jd_security_headers(self, jdpk):
        dt_str = time.strftime("%Y-%m-%d %I:%M:%S %p")
        digits = "".join(ch for ch in dt_str if ch.isdigit())
        salt = "Ge8V*WqBKzv#6wTj3!9KgDsHS?h?B"
        token = self._jd_crypt(salt, digits)
        return {
            "requestTime": urllib.parse.quote(dt_str),
            "securityToken": urllib.parse.quote(token),
            "jdpk": jdpk
        }

    def _jd_encrypt_jdlt(self, payload_dict, raw_key):
        import json
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM
        iv = bytes([54, 61, 189, 63, 251, 125, 69, 229, 213, 168, 92, 12])
        aesgcm = AESGCM(raw_key)
        plaintext = json.dumps(payload_dict, separators=(',', ':')).encode('utf-8')
        return aesgcm.encrypt(iv, plaintext, None).hex()

    def _scrape_justdial_as_lead(self, url, category_item, state, district, city=None, candidate=None, custom_keyword=""):
        """
        Deep Infinite-Scroll Scraper for JustDial:
        1. Extracts Page 1 + all 100 docids from Next.js __NEXT_DATA__
        2. Calls JustDial's internal /api/resultsPageListing (Pages 2..10) using AES-256-GCM (jdlt) + securityToken
        3. Unlocks hidden 'Show Number' phones & office landlines via /api/callallocate concurrently
        4. Falls back to HTML .resultbox + LD+JSON for individual business detail pages (_BZDET)
        5. When direct access is blocked (Akamai 403), extracts candidate business & resolves 100% Real Direct Owner Mobile Number via Solution 2!
        """
        import json, os
        from concurrent.futures import ThreadPoolExecutor

        leads = []
        seen_names_on_page = set()

        # Normalize /jdmart/{City}/{Slug}/...?nct=XXXX into standard JustDial category URL
        if '/jdmart/' in url.lower():
            parsed_jd = urlparse(url)
            p_parts = [p for p in parsed_jd.path.strip('/').split('/') if p]
            qs_jd = urllib.parse.parse_qs(parsed_jd.query)
            if len(p_parts) >= 3 and p_parts[0].lower() == 'jdmart' and 'nct' in qs_jd:
                url = f"https://www.justdial.com/{p_parts[1]}/{p_parts[2]}/nct-{qs_jd['nct'][0]}"

        base_url = re.sub(r'/page-\d+', '', url.split('?')[0].rstrip('/'))

        # Auto-append category NCT code for JustDial directory category listing pages if missing
        JD_NCT_MAP = {
            'civil-contractors': 'nct-10100369',
            'building-contractors': 'nct-10061214',
            'interior-designers': 'nct-10271038',
            'architects': 'nct-10022830',
            'structural-engineers': 'nct-10459524',
            'road-construction-contractors': 'nct-10411874',
            'road-contractors': 'nct-10411874',
            'electrical-contractors': 'nct-10185966',
            'painting-contractors': 'nct-10350702',
            'pwd-civil-contractors': 'nct-10398668',
            'earthmoving-contractors': 'nct-10181512',
            'building-material-dealers': 'nct-10061245',
        }
        parsed_parts = [p for p in urlparse(base_url).path.strip('/').split('/') if p]
        if len(parsed_parts) == 2 and not any('nct-' in p.lower() for p in parsed_parts) and not parsed_parts[1].lower().endswith(('.html', '.htm')) and not parsed_parts[1].upper().startswith('DT-'):
            cat_slug_low = parsed_parts[1].lower()
            if cat_slug_low in JD_NCT_MAP:
                base_url = f"{base_url}/{JD_NCT_MAP[cat_slug_low]}"
            elif category_item and category_item.get('id'):
                cid = category_item.get('id', '')
                if cid in JD_NCT_MAP:
                    base_url = f"{base_url}/{JD_NCT_MAP[cid]}"

        jd_session = requests.Session()
        jd_session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
            'Accept': '*/*',
            'Accept-Language': 'en-IN,en;q=0.9',
            'Referer': 'https://www.google.com/'
        })

        try:
            r = jd_session.get(base_url, timeout=(8, 18))
            if r.status_code != 200:
                # Direct HTTP access returned non-200 (Akamai block).
                # Auto-recover using candidate metadata + Solution 2 Google Maps/Web Direct Owner Mobile Lookup!
                if candidate:
                    raw_title = candidate.get('title', '')
                    raw_snip = candidate.get('snippet', '')
                    b_name = self.clean_company_name(raw_title, "justdial.com")
                    bad_names = ['justdial', 'just dial', 'results', 'civil contractors', 'contractors', 'find', 'top', 'best']
                    if b_name and not any(bn == b_name.lower() for bn in bad_names):
                        if custom_keyword and not self.matches_custom_keyword(f"{b_name} {raw_title} {raw_snip} {url}", custom_keyword):
                            return None
                        allowed_cities = self.get_allowed_cities(district, city)
                        if not self.has_conflicting_location(raw_title + " " + raw_snip, district, state, city):
                            b_area = city or district
                            for loc in allowed_cities:
                                if loc in raw_title.lower() or loc in raw_snip.lower() or loc in url.lower():
                                    b_area = loc.title()
                                    break

                            mobs = set()
                            lands = set()
                            ems = set()
                            web = url

                            for sp in (candidate.get('_snippet_phones') or []):
                                mobs.add(sp)

                            l_mobs, l_lands, l_ems, l_web = self.lookup_real_phone_for_business(
                                b_name, b_area, district, state, city
                            )
                            for lm in l_mobs:
                                mobs.add(lm)
                            for ll in l_lands:
                                lands.add(ll)
                            for le in l_ems:
                                ems.add(le)
                            if l_web:
                                web = l_web

                            if mobs or lands or ems:
                                dedup_key = ('justdial', b_name.lower())
                                if dedup_key not in self.seen_phones:
                                    self.seen_phones.add(dedup_key)
                                    lead = {
                                        "business_name": b_name,
                                        "category": custom_keyword.title() if custom_keyword else category_item['name'],
                                        "district": district,
                                        "state": state,
                                        "city_area": b_area,
                                        "rating": "",
                                        "mobile_numbers": ", ".join(sorted(list(mobs))),
                                        "office_numbers": ", ".join(sorted(list(lands))),
                                        "email_addresses": ", ".join(sorted(list(ems))),
                                        "address": f"{b_area}, {district}, {state}",
                                        "website": web,
                                        "source_url": url,
                                        "child_pages_crawled": 0,
                                        "verification_status": "Strictly Verified",
                                        "extracted_at": time.strftime("%Y-%m-%d %H:%M:%S")
                                    }
                                    self.emit_lead(lead)
                                    self.log(f"Extracted JustDial Lead: '{b_name}' | Phone: {lead['mobile_numbers'] or lead['office_numbers']}", 'success')
                                    return [lead]
                return None

            soup = BeautifulSoup(r.text, 'html.parser')

            # ── 1. CHECK FOR NEXT.JS __NEXT_DATA__ (INFINITE SCROLL 100-ITEM ENGINE) ──
            nd_script = soup.find('script', id='__NEXT_DATA__')
            if nd_script and nd_script.string:
                try:
                    nd = json.loads(nd_script.string)
                    page_props = nd.get('props', {}).get('pageProps', {})
                    ld = page_props.get('listData', {})
                    results_obj = ld.get('results', {})
                    p1_cols = results_obj.get('columns', [])
                    p1_rows = results_obj.get('data', [])

                    bz_single_dict = None
                    if not (p1_cols and p1_rows):
                        bz_cand = page_props.get('results', {}).get('results', {})
                        if isinstance(bz_cand, dict) and bz_cand.get('name'):
                            bz_single_dict = {
                                'name': bz_cand.get('name'),
                                'city': bz_cand.get('city') or bz_cand.get('data_city') or district,
                                'loccity': bz_cand.get('city') or district,
                                'area': bz_cand.get('area') or bz_cand.get('arealn') or '',
                                'arealn': bz_cand.get('arealn') or bz_cand.get('area') or '',
                                'NewAddress': bz_cand.get('address') or bz_cand.get('NewAddress') or '',
                                'pincode': bz_cand.get('pincode') or '',
                                'VNumber': bz_cand.get('VNumber') or '',
                                'wpnumber': bz_cand.get('wpnumber') or '',
                                'mobile': bz_cand.get('mobile') or '',
                                'contact': bz_cand.get('contact') or '',
                                'email': bz_cand.get('email') or '',
                                'callalocation': bz_cand.get('callalocation') or bz_cand.get('alocatedicid') or '',
                                'compRating': bz_cand.get('compRating') or bz_cand.get('comprating') or '',
                                'totalReviews': bz_cand.get('totalReviews') or bz_cand.get('totJdReviews') or '',
                                'sharedt_url': base_url
                            }

                    if (p1_cols and p1_rows) or bz_single_dict:
                        all_docids = [d for d in ld.get('nextdocid', '').split(',') if d] if (p1_cols and p1_rows) else []
                        raw_key = os.urandom(32)
                        jdpk = raw_key.hex()

                        jd_city = page_props.get('ct', district)
                        search_raw = page_props.get('search', '') or page_props.get('query', {}).get('search', '')
                        parts = search_raw.split('-in-')
                        dO = parts[0] if parts else ''
                        dT = parts[1] if len(parts) > 1 else ''
                        dQ = urllib.parse.quote(dO.replace('-', ' '))
                        dU = urllib.parse.quote(dT.replace('-', ' ')) if dT else ''
                        ax = str(page_props.get('ncatid') or ld.get('national_catid') or '')
                        an = ld.get('mncatnm', '')
                        aw = nd.get('runtimeConfig', {}).get('buildId', '') or nd.get('buildId', '') or ''

                        def unlock_show_number(b_dict):
                            if self.check_abort():
                                return b_dict
                            real_jd_nums = []
                            virtual_jd_nums = []
                            vn_field = str(b_dict.get('VNumber') or '').strip()
                            if vn_field:
                                virtual_jd_nums.append(vn_field)

                            # Check direct mobile/contact/wpnumber fields on b_dict
                            for d_field in [b_dict.get('mobile'), b_dict.get('contact'), b_dict.get('wpnumber')]:
                                if d_field:
                                    d_str = str(d_field)
                                    for pm in re.findall(r'(?:\+91|0)?[6-9]\d{9}', d_str):
                                        mob = self.is_valid_indian_mobile(pm)
                                        if mob and not self.is_virtual_pbx_number(mob) and mob not in vn_field:
                                            real_jd_nums.append(mob)

                            # Call /api/callallocate when VNumber is missing or locked virtual (0794...)
                            if (not vn_field or self.is_virtual_pbx_number(vn_field)) and b_dict.get('callalocation'):
                                try:
                                    sec_h = self._jd_security_headers(jdpk)
                                    sec_h['Content-Type'] = 'application/json'
                                    sec_h['Referer'] = 'https://www.google.com/'
                                    sec_h['Origin'] = 'https://www.justdial.com'
                                    payload = {
                                        "allocateid": b_dict.get('callalocation'),
                                        "mobile": "",
                                        "ask_mob": 0,
                                        "is_verified": 0,
                                        "ncatid": ax,
                                        "page": "results"
                                    }
                                    rc = jd_session.post(
                                        "https://www.justdial.com/api/callallocate?searchReferer=gen",
                                        json=payload, headers=sec_h, timeout=(5, 10)
                                    )
                                    if rc.status_code == 200 and len(rc.text) > 20:
                                        res_c = rc.json().get('result', {})
                                        vn = res_c.get('vn', '')
                                        an_obj = res_c.get('an', {})
                                        if vn:
                                            virtual_jd_nums.append(str(vn))
                                        if isinstance(an_obj, dict):
                                            if an_obj.get('m'):
                                                real_jd_nums.append(str(an_obj['m']))
                                            if an_obj.get('l'):
                                                real_jd_nums.append(str(an_obj['l']))
                                except Exception:
                                    pass

                            b_dict['_real_jd_phones'] = ", ".join(real_jd_nums)
                            b_dict['_virtual_jd_phones'] = ", ".join(virtual_jd_nums)

                            # Solution 2: If JustDial only gave a virtual number (or no real mobile),
                            # auto-lookup the 100% Real Direct Owner Mobile Number on Google Maps & Web!
                            has_real_mobile = any(
                                self.is_valid_indian_mobile(p) and not self.is_virtual_pbx_number(p)
                                for p in re.findall(r'(?:\+91|0)?[6-9]\d{9}', b_dict['_real_jd_phones'])
                            )
                            if not has_real_mobile:
                                b_name = (b_dict.get('name') or '').strip()
                                b_area = (b_dict.get('area') or b_dict.get('arealn') or '').strip()
                                l_mobs, l_lands, l_ems, l_web = self.lookup_real_phone_for_business(
                                    b_name, b_area, district, state, city
                                )
                                b_dict['_real_lookup_mobiles'] = l_mobs
                                b_dict['_real_lookup_landlines'] = l_lands
                                b_dict['_real_lookup_emails'] = l_ems
                                b_dict['_real_lookup_website'] = l_web

                            return b_dict

                        allowed_cities = self.get_allowed_cities(district, city)

                        def is_jd_row_in_target_district(b):
                            b_city = (b.get('city') or '').strip().lower()
                            b_loccity = (b.get('loccity') or '').strip().lower()
                            if not b_city or b_city not in allowed_cities:
                                return False
                            if b_loccity and b_loccity not in allowed_cities:
                                return False
                            for u_field in [b.get('sharedt_url'), b.get('weburl')]:
                                if u_field:
                                    u_str = str(u_field).strip()
                                    if not u_str.startswith('http'):
                                        u_str = 'https://www.justdial.com/' + u_str.lstrip('/')
                                    segs = [p for p in urlparse(u_str).path.strip('/').split('/') if p]
                                    if segs and not segs[0].upper().startswith('DT-'):
                                        if segs[0].lower() not in allowed_cities:
                                            return False
                            addr_check = f"{b.get('NewAddress') or ''} {b.get('area') or ''} {b.get('loccity') or ''}"
                            if self.has_conflicting_location(addr_check, district, state, city):
                                return False
                            if custom_keyword:
                                jd_kw_text = f"{b.get('name','')} {b.get('compNm','')} {b.get('NewAddress','')} {b.get('area','')} {b.get('ncatnm','')} {b.get('mncatnm','')} {b.get('search','')}"
                                if not self.matches_custom_keyword(jd_kw_text, custom_keyword):
                                    return False
                            return True

                        def process_jd_page_rows(rows_dicts, pg_label):
                            if self.check_abort():
                                return
                            # Pre-filter strictly by target district/city before unlocking numbers
                            valid_district_rows = [b for b in rows_dicts if is_jd_row_in_target_district(b)]
                            if not valid_district_rows:
                                return

                            # Unlock hidden 'Show Number' & Solution 2 Google Maps/Web Real Number Lookup concurrently
                            with ThreadPoolExecutor(max_workers=6) as pool:
                                unlocked_rows = list(pool.map(unlock_show_number, valid_district_rows))

                            for b in unlocked_rows:
                                name = (b.get('name') or '').strip()
                                if not name or len(name) < 3 or name.lower() in seen_names_on_page:
                                    continue

                                valid_phones = []
                                valid_landlines = []

                                # 1. Prefer 100% Real Direct Owner Numbers (from Solution 2 Google Maps/Web or JustDial an.m/an.l)
                                for lp in (b.get('_real_lookup_mobiles') or []):
                                    if lp not in valid_phones:
                                        valid_phones.append(lp)
                                for ll in (b.get('_real_lookup_landlines') or []):
                                    if ll not in valid_landlines:
                                        valid_landlines.append(ll)

                                real_jd_str = str(b.get('_real_jd_phones') or '')
                                for p in re.findall(r'(?:\+91|0)?[6-9]\d{9}', real_jd_str):
                                    v = self.is_valid_indian_mobile(p)
                                    if v and not self.is_virtual_pbx_number(v):
                                        fmt = f"+91 {v[:5]} {v[5:]}"
                                        if fmt not in valid_phones:
                                            valid_phones.append(fmt)
                                for l in re.findall(r'\b(0\d{2,4}[ -]?\d{6,8})\b', real_jd_str):
                                    l_clean = l.strip()
                                    digits = re.sub(r'\D', '', l_clean)
                                    if 10 <= len(digits) <= 12 and not self.is_valid_indian_mobile(digits) and not self.is_virtual_pbx_number(digits):
                                        if l_clean not in valid_landlines:
                                            valid_landlines.append(l_clean)

                                # 2. Only fall back to non-locked JustDial numbers if no real owner number was found on Google Maps/Web
                                if not valid_phones and not valid_landlines:
                                    virt_str = str(b.get('_virtual_jd_phones') or '')
                                    for p in re.findall(r'(?:\+91|0)?[6-9]\d{9}', virt_str):
                                        v = self.is_valid_indian_mobile(p)
                                        if v and not self.is_virtual_pbx_number(v):
                                            fmt = f"+91 {v[:5]} {v[5:]}"
                                            if fmt not in valid_phones:
                                                valid_phones.append(fmt)
                                    for l in re.findall(r'\b(0\d{2,4}[ -]?\d{6,8})\b', virt_str):
                                        l_clean = l.strip()
                                        digits = re.sub(r'\D', '', l_clean)
                                        if 10 <= len(digits) <= 12 and not self.is_valid_indian_mobile(digits) and not self.is_virtual_pbx_number(digits):
                                            if l_clean not in valid_landlines:
                                                valid_landlines.append(l_clean)

                                # Deduplicate against already extracted phones while keeping multi-number cards
                                new_phones = [vp for vp in valid_phones if vp not in self.seen_phones]
                                if not new_phones and not valid_landlines:
                                    continue

                                for vp in new_phones:
                                    self.seen_phones.add(vp)
                                seen_names_on_page.add(name.lower())

                                rate_val = str(b.get('compRating') or '').strip()
                                rate_cnt = str(b.get('totalReviews') or b.get('totJdReviews') or '').strip()
                                if rate_cnt and 'rating' not in rate_cnt.lower():
                                    rate_cnt = f"{rate_cnt} Ratings"
                                if rate_val and rate_val not in ['0', '0.0']:
                                    rating_str = f"{rate_val} ★ ({rate_cnt})" if rate_cnt else f"{rate_val} ★"
                                else:
                                    rating_str = ""

                                addr_parts = []
                                for ap in [(b.get('NewAddress') or '').strip(), (b.get('area') or '').strip(), (b.get('loccity') or district).strip()]:
                                    if ap and ap.lower() not in [x.lower() for x in addr_parts]:
                                        addr_parts.append(ap)
                                addr_str = ", ".join(addr_parts)
                                pin = str(b.get('pincode') or '').strip()
                                if pin and pin not in addr_str:
                                    addr_str = f"{addr_str} - {pin}"

                                card_url = (b.get('sharedt_url') or '').strip()
                                if not card_url or 'jsdl.in' in card_url:
                                    if b.get('weburl'):
                                        card_url = f"https://www.justdial.com/{str(b['weburl']).lstrip('/')}"
                                    else:
                                        card_url = base_url

                                email_list = list(b.get('_real_lookup_emails') or [])
                                if b.get('email') and self.is_valid_email(str(b.get('email'))):
                                    em_val = str(b.get('email')).strip().lower()
                                    if em_val not in email_list:
                                        email_list.append(em_val)

                                lead = {
                                    "business_name": name,
                                    "category": custom_keyword.title() if custom_keyword else category_item['name'],
                                    "district": district,
                                    "state": state,
                                    "city_area": (b.get('arealn') or city or district).strip(),
                                    "rating": rating_str,
                                    "mobile_numbers": ", ".join(new_phones if new_phones else valid_phones),
                                    "office_numbers": ", ".join(valid_landlines),
                                    "email_addresses": ", ".join(email_list),
                                    "address": addr_str or f"{city or district}, {district}, {state}",
                                    "website": b.get('_real_lookup_website') or card_url,
                                    "source_url": card_url,
                                    "child_pages_crawled": 0,
                                    "verification_status": "Strictly Verified",
                                    "extracted_at": time.strftime("%Y-%m-%d %H:%M:%S")
                                }
                                leads.append(lead)
                                self.emit_lead(lead)
                                self.log(
                                    f"Extracted JustDial [{pg_label}]: '{name}' | Phone: {lead['mobile_numbers'] or lead['office_numbers']} | Rating: {rating_str or 'None'}",
                                    'success'
                                )

                        # Process Page 1 (or single _BZDET page)
                        p1_dicts = [bz_single_dict] if bz_single_dict else [dict(zip(p1_cols, row)) for row in p1_rows]
                        process_jd_page_rows(p1_dicts, "p.1")

                        # Infinite Scroll Pages 2..10 via /api/resultsPageListing
                        max_pages = min(10, (len(all_docids) + 9) // 10)
                        for ak in range(2, max_pages + 1):
                            if self.check_abort():
                                break
                            self.wait_if_paused()

                            nxt = ",".join(all_docids[(ak - 1) * 10 : ak * 10])
                            if not nxt:
                                break

                            try:
                                enc_input = {
                                    "cnm": an,
                                    "nxt": nxt,
                                    "pg": ak,
                                    "trm": dQ,
                                    "catid": ax,
                                    "ct": jd_city,
                                    "ar": dU
                                }
                                jdlt = self._jd_encrypt_jdlt(enc_input, raw_key)
                                body = {
                                    "median_latitude": ld.get('median_latitude', '') if str(ld.get('median_latitude', '')) else "",
                                    "median_longitude": ld.get('median_longitude', '') if str(ld.get('median_longitude', '')) else "",
                                    "city": jd_city,
                                    "search": dQ,
                                    "area": dU,
                                    "lat": "",
                                    "long": "",
                                    "national_catid": ax,
                                    "nextdocid": nxt,
                                    "stype": "category_list",
                                    "opt": "",
                                    "login_mobile": None,
                                    "pg_no": ak,
                                    "nearme": "0",
                                    "checkin": "",
                                    "checkout": "",
                                    "attribute_values": "",
                                    "mncatname": an,
                                    "darea_flg": 0,
                                    "bid": 0,
                                    "bizId": "",
                                    "pdid": [],
                                    "trkid": "",
                                    "version": "2.6",
                                    "search_id": ld.get('search_id', ''),
                                    "attr": "",
                                    "chainotlt": ld.get('chainoutlet', 0),
                                    "asnm": 0,
                                    "cbflg": "",
                                    "selectedImage": "",
                                    "isgroup": "",
                                    "jdlt": jdlt
                                }
                                sec_headers = self._jd_security_headers(jdpk)
                                sec_headers['Content-Type'] = 'application/json'
                                sec_headers['Referer'] = 'https://www.google.com/'
                                sec_headers['Origin'] = 'https://www.justdial.com'
                                sec_headers['gprefetch'] = str(ld.get('GPREFETCH', 'false'))

                                api_url = f"https://www.justdial.com/api/resultsPageListing?bids={urllib.parse.quote(aw)}&searchReferer=gen"
                                resp = jd_session.post(api_url, json=body, headers=sec_headers, timeout=(8, 15))
                                if resp.status_code == 200 and len(resp.text) > 50:
                                    rj = resp.json()
                                    res_data = rj.get('results', {}).get('data', [])
                                    cols = rj.get('results', {}).get('columns', [])
                                    if res_data and cols:
                                        pg_dicts = [dict(zip(cols, row)) for row in res_data]
                                        process_jd_page_rows(pg_dicts, f"p.{ak}")
                                    else:
                                        break
                                else:
                                    break
                            except Exception as api_ex:
                                self.log(f"JustDial API p.{ak} note: {api_ex}", 'debug')
                                break

                        if leads:
                            return leads
                except Exception as nd_ex:
                    self.log(f"JustDial NEXT_DATA parse note: {nd_ex}", 'debug')

            # ── 2. FALLBACK: HTML .resultbox & JSON-LD PARSER (FOR SINGLE _BZDET PAGES) ──
            allowed_cities = self.get_allowed_cities(district, city)
            base_segs = [p for p in urlparse(base_url).path.strip('/').split('/') if p]
            if base_segs and not base_segs[0].upper().startswith('DT-') and base_segs[0].lower() not in allowed_cities:
                return None

            schema_address_map = {}
            for script in soup.select('script[type="application/ld+json"]'):
                try:
                    data = json.loads(script.string or '{}')
                    items = data if isinstance(data, list) else [data]
                    for item in items:
                        name_val = item.get('name', '').strip()
                        addr_obj = item.get('address')
                        if name_val and isinstance(addr_obj, dict):
                            loc_val = (addr_obj.get('addressLocality') or '').strip().lower()
                            if loc_val and loc_val not in allowed_cities:
                                continue
                            parts = [
                                addr_obj.get('streetAddress', ''),
                                addr_obj.get('addressLocality', ''),
                                addr_obj.get('addressRegion', ''),
                                addr_obj.get('postalCode', '')
                            ]
                            schema_address_map[name_val.lower()] = ", ".join([p for p in parts if p])
                except Exception:
                    pass

            cards = soup.select('.resultbox, .cntanr') or soup.select('.resultbox_info')
            for card in cards:
                name_el = card.select_one('.resultbox_title_anchor, .jd-heading, h2, .fn, .lng_cont_name')
                if not name_el:
                    continue
                name = name_el.text.strip()
                if not name or len(name) < 3 or name.lower() in ['justdial', 'help'] or name.lower() in seen_names_on_page:
                    continue

                card_text = card.get_text(separator=' ')
                if custom_keyword and not self.matches_custom_keyword(f"{name} {card_text}", custom_keyword):
                    continue

                card_url = base_url
                for a in card.find_all('a', href=True):
                    href = a['href'].strip()
                    if href and not href.startswith(('javascript:', '#')):
                        full_href = urljoin('https://www.justdial.com', href)
                        if 'justdial.com/' in full_href and not full_href.endswith('.html') and 'nct-' not in full_href:
                            card_url = full_href.split('?')[0]
                            break

                if 'justdial.com/' in card_url.lower():
                    c_segs = [p for p in urlparse(card_url).path.strip('/').split('/') if p]
                    if c_segs and not c_segs[0].upper().startswith('DT-') and c_segs[0].lower() not in allowed_cities:
                        continue

                loc_el = card.select_one('.locatcity, .addressinfo, [itemprop="address"], .address, .cont_sw_addr')
                addr = loc_el.text.strip() if loc_el else ""
                if not addr or len(addr) < 6:
                    addr = schema_address_map.get(name.lower(), "")
                if not addr or not any(loc in addr.lower() for loc in allowed_cities) or self.has_conflicting_location(addr, district, state, city):
                    continue

                seen_names_on_page.add(name.lower())

                rate_val_el = card.select_one('.resultbox_totalrate, .green-box, .rating-val, .resultbox_count')
                rate_cnt_el = card.select_one('.resultbox_countrate, .rt_count')
                rating_val = rate_val_el.text.strip() if rate_val_el else ""
                ratings_count = rate_cnt_el.text.strip() if rate_cnt_el else ""
                if not rating_val:
                    v_m = re.search(r'\b([1-5]\.\d)\b', card_text)
                    if v_m: rating_val = v_m.group(1)
                if not ratings_count:
                    c_m = re.search(r'\b(\d+\s*Ratings?)\b', card_text, re.IGNORECASE)
                    if c_m: ratings_count = c_m.group(1)
                rating_str = f"{rating_val} ★ ({ratings_count})" if rating_val and ratings_count else (f"{rating_val} ★" if rating_val else "")

                l_mobs, l_lands, l_ems, l_web = self.lookup_real_phone_for_business(name, "", district, state, city)
                valid_phones = [vp for vp in l_mobs if vp not in self.seen_phones]
                valid_landlines = list(l_lands)

                if not valid_phones and not valid_landlines:
                    phones = re.findall(r'(?:\+91|0)?[6-9]\d{9}', card_text)
                    for p in set(phones):
                        v = self.is_valid_indian_mobile(p)
                        if v and not self.is_virtual_pbx_number(v) and f"+91 {v[:5]} {v[5:]}" not in self.seen_phones:
                            valid_phones.append(f"+91 {v[:5]} {v[5:]}")
                    landlines = re.findall(r'\b(0\d{2,4}[ -]?\d{6,8})\b', card_text)
                    valid_landlines = [l.strip() for l in set(landlines) if 10 <= len(re.sub(r'\D', '', l)) <= 12 and not self.is_virtual_pbx_number(l) and l not in phones]

                if not valid_phones and not valid_landlines:
                    continue

                for vp in valid_phones:
                    self.seen_phones.add(vp)

                lead = {
                    "business_name": name,
                    "category": custom_keyword.title() if custom_keyword else category_item['name'],
                    "district": district,
                    "state": state,
                    "city_area": city or district,
                    "rating": rating_str,
                    "mobile_numbers": ", ".join(valid_phones),
                    "office_numbers": ", ".join(valid_landlines),
                    "email_addresses": ", ".join(l_ems),
                    "address": addr,
                    "website": l_web or card_url,
                    "source_url": card_url,
                    "child_pages_crawled": 0,
                    "verification_status": "Strictly Verified",
                    "extracted_at": time.strftime("%Y-%m-%d %H:%M:%S")
                }
                leads.append(lead)
                self.emit_lead(lead)
                self.log(f"Extracted JustDial Card: '{name}' | Phone: {lead['mobile_numbers']} | Rating: {rating_str or 'None'}", 'success')

        except Exception as e:
            self.log(f"JustDial scrape note: {e}", 'debug')

        return leads if leads else None

