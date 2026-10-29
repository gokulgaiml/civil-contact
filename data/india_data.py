"""
Complete PAN-India Geographic Data & Construction Industry Taxonomy.
Includes all 28 States and 8 Union Territories with official districts,
along with verified construction business categories and keyword signatures.
"""

INDIAN_STATES_AND_DISTRICTS = {
    "Andhra Pradesh": [
        "Alluri Sitharama Raju", "Anakapalli", "Ananthapuramu", "Annamayya", "Bapatla", 
        "Chittoor", "Dr. B.R. Ambedkar Konaseema", "East Godavari", "Eluru", "Guntur", 
        "Kakinada", "Krishna", "Kurnool", "Nandyal", "NTR", "Palnadu", "Parvathipuram Manyam", 
        "Prakasam", "Srikakulam", "Sri Potti Sriramulu Nellore", "Sri Sathya Sai", 
        "Tirupati", "Visakhapatnam", "Vizianagaram", "West Godavari", "YSR Kadapa"
    ],
    "Arunachal Pradesh": [
        "Anjaw", "Changlang", "Dibang Valley", "East Kameng", "East Siang", "Kamle", 
        "Kra Daadi", "Kurung Kumey", "Lepa Rada", "Lohit", "Longding", "Lower Dibang Valley", 
        "Lower Siang", "Lower Subansiri", "Namsai", "Pakke Kessang", "Papum Pare", 
        "Shi Yomi", "Siang", "Tawang", "Tirap", "Upper Siang", "Upper Subansiri", "West Kameng", "West Siang"
    ],
    "Assam": [
        "Baksa", "Barpeta", "Biswanath", "Bongaigaon", "Cachar", "Charaideo", "Chirang", 
        "Darrang", "Dhemaji", "Dhubri", "Dibrugarh", "Dima Hasao", "Goalpara", "Golaghat", 
        "Hailakandi", "Hojai", "Jorhat", "Kamrup", "Kamrup Metropolitan", "Karbi Anglong", 
        "Karimganj", "Kokrajhar", "Lakhimpur", "Majuli", "Morigaon", "Nagaon", "Nalbari", 
        "Sivasagar", "Sonitpur", "South Salmara-Mankachar", "Tinsukia", "Udalguri", "West Karbi Anglong"
    ],
    "Bihar": [
        "Araria", "Arwal", "Aurangabad", "Banka", "Begusarai", "Bhagalpur", "Bhojpur", 
        "Buxar", "Darbhanga", "East Champaran", "Gaya", "Gopalganj", "Jamui", "Jehanabad", 
        "Kaimur", "Katihar", "Khagaria", "Kishanganj", "Lakhisarai", "Madhepura", "Madhubani", 
        "Munger", "Muzaffarpur", "Nalanda", "Nawada", "Patna", "Purnia", "Rohtas", "Saharsa", 
        "Samastipur", "Saran", "Sheikhpura", "Sheohar", "Sitamarhi", "Siwan", "Supaul", 
        "Vaishali", "West Champaran"
    ],
    "Chhattisgarh": [
        "Balod", "Baloda Bazar", "Balrampur", "Bastar", "Bemetara", "Bijapur", "Bilaspur", 
        "Dantewada", "Dhamtari", "Durg", "Gariaband", "Gaurela Pendra Marwahi", "Janjgir-Champa", 
        "Jashpur", "Kabirdham", "Kanker", "Khairagarh-Chhuikhadan-Gandai", "Kondagaon", 
        "Korba", "Koriya", "Mahasamund", "Manendragarh-Chirmiri-Bharatpur", "Mohla-Manpur-Ambagarh Chowki", 
        "Mungeli", "Narayanpur", "Raigarh", "Raipur", "Rajnandgaon", "Sakti", "Sarangarh-Bilaigarh", 
        "Sukma", "Surajpur", "Surguja"
    ],
    "Goa": [
        "North Goa", "South Goa"
    ],
    "Gujarat": [
        "Ahmedabad", "Amreli", "Anand", "Aravalli", "Banaskantha", "Bharuch", "Bhavnagar", 
        "Botad", "Chhota Udaipur", "Dahod", "Dang", "Devbhumi Dwarka", "Gandhinagar", 
        "Gir Somnath", "Jamnagar", "Junagadh", "Kheda", "Kutch", "Mahisagar", "Mehsana", 
        "Morbi", "Narmada", "Navsari", "Panchmahal", "Patan", "Porbandar", "Rajkot", 
        "Sabarkantha", "Surat", "Surendranagar", "Tapi", "Vadodara", "Valsad"
    ],
    "Haryana": [
        "Ambala", "Bhiwani", "Charkhi Dadri", "Faridabad", "Fatehabad", "Gurugram", 
        "Hisar", "Jhajjar", "Jind", "Kaithal", "Karnal", "Kurukshetra", "Mahendragarh", 
        "Nuh", "Palwal", "Panchkula", "Panipat", "Rewari", "Rohtak", "Sirsa", "Sonipat", "Yamunanagar"
    ],
    "Himachal Pradesh": [
        "Bilaspur", "Chamba", "Hamirpur", "Kangra", "Kinnaur", "Kullu", "Lahaul and Spiti", 
        "Mandi", "Shimla", "Sirmaur", "Solan", "Una"
    ],
    "Jharkhand": [
        "Bokaro", "Chatra", "Deoghar", "Dhanbad", "Dumka", "East Singhbhum", "Garhwa", 
        "Giridih", "Godda", "Gumla", "Hazaribagh", "Jamtara", "Khunti", "Koderma", 
        "Latehar", "Lohardaga", "Pakur", "Palamu", "Ramgarh", "Ranchi", "Sahebganj", 
        "Seraikela Kharsawan", "Simdega", "West Singhbhum"
    ],
    "Karnataka": [
        "Bagalkote", "Ballari", "Belagavi", "Bengaluru Rural", "Bengaluru Urban", "Bidar", 
        "Chamarajanagar", "Chikkaballapura", "Chikkamagaluru", "Chitradurga", "Dakshina Kannada", 
        "Davanagere", "Dharwad", "Gadag", "Hassan", "Haveri", "Kalaburagi", "Kodagu", 
        "Kolar", "Koppal", "Mandya", "Mysuru", "Raichur", "Ramanagara", "Shivamogga", 
        "Tumakuru", "Udupi", "Uttara Kannada", "Vijayanagara", "Vijayapura", "Yadgir"
    ],
    "Kerala": [
        "Alappuzha", "Ernakulam", "Idukki", "Kannur", "Kasaragod", "Kollam", "Kottayam", 
        "Kozhikode", "Malappuram", "Palakkad", "Pathanamthitta", "Thiruvananthapuram", "Thrissur", "Wayanad"
    ],
    "Madhya Pradesh": [
        "Agar Malwa", "Alirajpur", "Anuppur", "Ashoknagar", "Balaghat", "Barwani", "Betul", 
        "Bhind", "Bhopal", "Burhanpur", "Chhatarpur", "Chhindwara", "Damoh", "Datia", 
        "Dewas", "Dhar", "Dindori", "Guna", "Gwalior", "Harda", "Hoshangabad", "Indore", 
        "Jabalpur", "Jhabua", "Katni", "Khandwa", "Khargone", "Maihar", "Mandla", "Mandsaur", 
        "Morena", "Narsinghpur", "Neemuch", "Niwari", "Panna", "Raisen", "Rajgarh", "Ratlam", 
        "Rewa", "Sagar", "Satna", "Sehore", "Seoni", "Shahdol", "Shajapur", "Sheopur", 
        "Shivpuri", "Sidhi", "Singrauli", "Tikamgarh", "Ujjain", "Umaria", "Vidisha"
    ],
    "Maharashtra": [
        "Ahmednagar", "Akola", "Amravati", "Chhatrapati Sambhajinagar", "Beed", "Bhandara", 
        "Buldhana", "Chandrapur", "Dhule", "Gadchiroli", "Gondia", "Hingoli", "Jalgaon", 
        "Jalna", "Kolhapur", "Latur", "Mumbai City", "Mumbai Suburban", "Nagpur", "Nanded", 
        "Nandurbar", "Nashik", "Dharashiv", "Palghar", "Parbhani", "Pune", "Raigad", 
        "Ratnagiri", "Sangli", "Satara", "Sindhudurg", "Solapur", "Thane", "Wardha", "Washim", "Yavatmal"
    ],
    "Manipur": [
        "Bishnupur", "Chandel", "Churachandpur", "Imphal East", "Imphal West", "Jiribam", 
        "Kakching", "Kamjong", "Kangpokpi", "Noney", "Pherzawl", "Senapati", "Tamenglong", 
        "Tengnoupal", "Thoubal", "Ukhrul"
    ],
    "Meghalaya": [
        "East Garo Hills", "East Jaintia Hills", "East Khasi Hills", "Eastern West Khasi Hills", 
        "North Garo Hills", "Ri Bhoi", "South Garo Hills", "South West Garo Hills", 
        "South West Khasi Hills", "West Garo Hills", "West Jaintia Hills", "West Khasi Hills"
    ],
    "Mizoram": [
        "Aizawl", "Champhai", "Hnahthial", "Khawzawl", "Kolasib", "Lawngtlai", "Lunglei", 
        "Mamit", "Saiha", "Saitual", "Serchhip"
    ],
    "Nagaland": [
        "Chumoukedima", "Dimapur", "Kiphire", "Kohima", "Longleng", "Mokokchung", "Mon", 
        "Niuland", "Noklak", "Peren", "Phek", "Shamator", "Tseminyu", "Tuensang", "Wokha", "Zunheboto"
    ],
    "Odisha": [
        "Angul", "Balangir", "Balasore", "Bargarh", "Bhadrak", "Boudh", "Cuttack", 
        "Deogarh", "Dhenkanal", "Gajapati", "Ganjam", "Jagatsinghpur", "Jajpur", "Jharsuguda", 
        "Kalahandi", "Kandhamal", "Kendrapara", "Kendujhar", "Khordha", "Koraput", "Malkangiri", 
        "Mayurbhanj", "Nabarangpur", "Nayagarh", "Nuapada", "Puri", "Rayagada", "Sambalpur", 
        "Subarnapur", "Sundargarh"
    ],
    "Punjab": [
        "Amritsar", "Barnala", "Bathinda", "Faridkot", "Fatehgarh Sahib", "Fazilka", 
        "Ferozepur", "Gurdaspur", "Hoshiarpur", "Jalandhar", "Kapurthala", "Ludhiana", 
        "Malerkotla", "Mansa", "Moga", "Muktsar", "Pathankot", "Patiala", "Rupnagar", 
        "Sahibzada Ajit Singh Nagar (Mohali)", "Sangrur", "Shahid Bhagat Singh Nagar", "Tarn Taran"
    ],
    "Rajasthan": [
        "Ajmer", "Alwar", "Anupgarh", "Balotra", "Banswara", "Baran", "Barmer", "Beawar", 
        "Bharatpur", "Bhilwara", "Bikaner", "Bundi", "Chittorgarh", "Churu", "Dausa", 
        "Deeg", "Dholpur", "Didwana-Kuchaman", "Dudu", "Dungarpur", "Ganganagar", 
        "Gangapur City", "Hanumangarh", "Jaipur", "Jaipur Rural", "Jaisalmer", "Jalore", 
        "Jhalawar", "Jhunjhunu", "Jodhpur", "Jodhpur Rural", "Karauli", "Kekri", "Khairthal-Tijara", 
        "Kota", "Kotputli-Behror", "Nagaur", "Neem Ka Thana", "Pali", "Phalodi", "Pratapgarh", 
        "Rajsamand", "Salumbar", "Sanchore", "Sawai Madhopur", "Shahpura", "Sikar", "Sirohi", "Tonk", "Udaipur"
    ],
    "Sikkim": [
        "Gangtok", "Gyalshing", "Mangan", "Namchi", "Pakyong", "Soreng"
    ],
    "Tamil Nadu": [
        "Ariyalur", "Chengalpattu", "Chennai", "Coimbatore", "Cuddalore", "Dharmapuri", 
        "Dindigul", "Erode", "Kallakurichi", "Kanchipuram", "Kanyakumari", "Karur", 
        "Krishnagiri", "Madurai", "Mayiladuthurai", "Nagapattinam", "Namakkal", "Nilgiris", 
        "Perambalur", "Pudukkottai", "Ramanathapuram", "Ranipet", "Salem", "Sivaganga", 
        "Tenkasi", "Thanjavur", "Theni", "Thoothukudi", "Tiruchirappalli", "Tirunelveli", 
        "Tirupathur", "Tiruppur", "Tiruvallur", "Tiruvannamalai", "Tiruvarur", "Vellore", 
        "Viluppuram", "Virudhunagar"
    ],
    "Telangana": [
        "Adilabad", "Bhadradri Kothagudem", "Hanamkonda", "Hyderabad", "Jagtial", "Jangaon", 
        "Jayashankar Bhupalpally", "Jogulamba Gadwal", "Kamareddy", "Karimnagar", "Khammam", 
        "Kumuram Bheem Asifabad", "Mahabubabad", "Mahabubnagar", "Mancherial", "Medak", 
        "Medchal-Malkajgiri", "Mulugu", "Nagarkurnool", "Nalgonda", "Narayanpet", "Nirmal", 
        "Nizamabad", "Peddapalli", "Rajanna Sircilla", "Ranga Reddy", "Sangareddy", 
        "Siddipet", "Suryapet", "Vikarabad", "Wanaparthy", "Warangal", "Yadadri Bhuvanagiri"
    ],
    "Tripura": [
        "Dhalai", "Gomati", "Khowai", "North Tripura", "Sepahijala", "South Tripura", 
        "Unakoti", "West Tripura"
    ],
    "Uttar Pradesh": [
        "Agra", "Aligarh", "Ambedkar Nagar", "Amethi", "Amroha", "Auraiya", "Ayodhya", 
        "Azamgarh", "Baghpat", "Bahraich", "Ballia", "Balrampur", "Banda", "Barabanki", 
        "Bareilly", "Basti", "Bhadohi", "Bijnor", "Budaun", "Bulandshahr", "Chandauli", 
        "Chitrakoot", "Deoria", "Etah", "Etawah", "Farrukhabad", "Fatehpur", "Firozabad", 
        "Gautam Buddha Nagar (Noida)", "Ghaziabad", "Ghazipur", "Gonda", "Gorakhpur", 
        "Hamirpur", "Hapur", "Hardoi", "Hathras", "Jalaun", "Jaunpur", "Jhansi", 
        "Kannauj", "Kanpur Dehat", "Kanpur Nagar", "Kasganj", "Kaushambi", "Kheri", 
        "Kushinagar", "Lalitpur", "Lucknow", "Maharajganj", "Mahoba", "Mainpuri", 
        "Mathura", "Mau", "Meerut", "Mirzapur", "Moradabad", "Muzaffarnagar", "Pilibhit", 
        "Pratapgarh", "Prayagraj", "Raebareli", "Rampur", "Saharanpur", "Sambhal", 
        "Sant Kabir Nagar", "Shahjahanpur", "Shamli", "Shravasti", "Siddharthnagar", 
        "Sitapur", "Sonbhadra", "Sultanpur", "Unnao", "Varanasi"
    ],
    "Uttarakhand": [
        "Almora", "Bageshwar", "Chamoli", "Champawat", "Dehradun", "Haridwar", 
        "Nainital", "Pauri Garhwal", "Pithoragarh", "Rudraprayag", "Tehri Garhwal", 
        "Udham Singh Nagar", "Uttarkashi"
    ],
    "West Bengal": [
        "Alipurduar", "Bankura", "Birbhum", "Cooch Behar", "Dakshin Dinajpur", "Darjeeling", 
        "Hooghly", "Howrah", "Jalpaiguri", "Jhargram", "Kalimpong", "Kolkata", "Malda", 
        "Murshidabad", "Nadia", "North 24 Parganas", "Paschim Bardhaman", "Paschim Medinipur", 
        "Purba Bardhaman", "Purba Medinipur", "Purulia", "South 24 Parganas", "Uttar Dinajpur"
    ],
    "Andaman and Nicobar Islands": [
        "Nicobar", "North and Middle Andaman", "South Andaman"
    ],
    "Chandigarh": [
        "Chandigarh"
    ],
    "Dadra and Nagar Haveli and Daman and Diu": [
        "Dadra and Nagar Haveli", "Daman", "Diu"
    ],
    "Delhi": [
        "Central Delhi", "East Delhi", "New Delhi", "North Delhi", "North East Delhi", 
        "North West Delhi", "Shahdara", "South Delhi", "South East Delhi", "South West Delhi", "West Delhi"
    ],
    "Jammu and Kashmir": [
        "Anantnag", "Bandipora", "Baramulla", "Budgam", "Doda", "Ganderbal", "Jammu", 
        "Kathua", "Kishtwar", "Kulgam", "Kupwara", "Poonch", "Pulwama", "Rajouri", 
        "Ramban", "Reasi", "Samba", "Shopian", "Srinagar", "Udhampur"
    ],
    "Ladakh": [
        "Kargil", "Leh"
    ],
    "Lakshadweep": [
        "Lakshadweep"
    ],
    "Puducherry": [
        "Karaikal", "Mahe", "Puducherry", "Yanam"
    ]
}

# Categorization of construction business types with specific keyword patterns
CONSTRUCTION_CATEGORIES = [
    {
        "id": "civil_contractors",
        "name": "Civil Contractors & Infrastructure Developers",
        "search_terms": [
            "civil contractor", "civil engineering contractor", "civil works", 
            "infrastructure contractor", "civil construction company"
        ],
        "keywords": [
            "civil", "contractor", "civil work", "infrastructure", "earthwork", 
            "structural work", "civil construction", "engineering contractor"
        ]
    },
    {
        "id": "building_contractors",
        "name": "Building Contractors & Commercial Builders",
        "search_terms": [
            "building contractor", "commercial builders", "residential building contractor", 
            "turnkey builder", "construction company"
        ],
        "keywords": [
            "building contractor", "builder", "construction", "residential project", 
            "commercial building", "apartments", "villas", "turnkey construction"
        ]
    },
    {
        "id": "architects_designers",
        "name": "Architects & Architectural Planners",
        "search_terms": [
            "architects", "architectural firm", "building designer", "registered architect"
        ],
        "keywords": [
            "architect", "architectural", "blueprint", "building plan", "elevation", 
            "landscape architect", "design studio", "coa registered"
        ]
    },
    {
        "id": "structural_engineers",
        "name": "Structural Engineers & Design Consultants",
        "search_terms": [
            "structural engineer", "structural consultant", "rcc design consultant", "structural stability certificate"
        ],
        "keywords": [
            "structural", "structural engineer", "rcc design", "steel structure", 
            "foundation design", "structural audit", "stability certificate"
        ]
    },
    {
        "id": "interior_contractors",
        "name": "Interior Contractors & Fit-Out Specialists",
        "search_terms": [
            "interior contractor", "commercial interior fit-out", "turnkey interior contractor"
        ],
        "keywords": [
            "interior", "interior contractor", "fit-out", "false ceiling", "modular", 
            "carpentry work", "flooring contractor", "interior turnkey"
        ]
    },
    {
        "id": "road_highway_contractors",
        "name": "Road, Highway & Paving Contractors",
        "search_terms": [
            "road contractor", "asphalt paving contractor", "highway construction contractor", "bitumen road work"
        ],
        "keywords": [
            "road contractor", "highway", "paving", "tar road", "asphalt", 
            "bitumen", "paver blocks", "pwd road work"
        ]
    },
    {
        "id": "mep_electrical_plumbing",
        "name": "MEP, Electrical & Plumbing Contractors",
        "search_terms": [
            "mep contractor", "licensed electrical contractor", "plumbing contractor", "sanitary contractor"
        ],
        "keywords": [
            "mep", "electrical contractor", "plumbing", "sanitary", "hvac", 
            "firefighting contractor", "pipeline contractor", "ht panel"
        ]
    },
    {
        "id": "painting_waterproofing",
        "name": "Painting & Waterproofing Contractors",
        "search_terms": [
            "waterproofing contractor", "commercial painting contractor", "damp proofing contractor"
        ],
        "keywords": [
            "waterproofing", "damp proofing", "terrace waterproofing", "painting contractor", 
            "exterior painting", "epoxy flooring", "chemical waterproofing"
        ]
    },
    {
        "id": "govt_approved_contractors",
        "name": "Government Approved (PWD/CPWD/Class-1) Contractors",
        "search_terms": [
            "pwd contractor", "govt approved civil contractor", "cpwd registered contractor", "class 1 contractor"
        ],
        "keywords": [
            "pwd", "cpwd", "class 1 contractor", "class-i", "govt approved", 
            "tender contractor", "government registered", "municipal contractor"
        ]
    },
    {
        "id": "earthmoving_demolition",
        "name": "Earthmoving, Demolition & Foundation Contractors",
        "search_terms": [
            "earthmoving contractor", "excavation contractor", "piling contractor", "demolition contractor"
        ],
        "keywords": [
            "earthmoving", "excavation", "jcb", "piling contractor", "demolition", 
            "borewell", "soil testing", "deep foundation"
        ]
    },
    {
        "id": "rmc_materials_suppliers",
        "name": "Ready Mix Concrete (RMC) & Material Suppliers",
        "search_terms": [
            "ready mix concrete rmc supplier", "building materials supplier", "tmt steel cement supplier"
        ],
        "keywords": [
            "rmc", "ready mix concrete", "batching plant", "cement dealer", 
            "tmt steel", "blue metal supplier", "aggregates"
        ]
    }
]

# Standard STD code prefixes for Indian cities to recognize landline phone numbers
INDIAN_STD_CODES = {
    "Erode": "0424",
    "Chennai": "044",
    "Coimbatore": "0422",
    "Madurai": "0452",
    "Tiruchirappalli": "0431",
    "Salem": "0427",
    "Tiruppur": "0421",
    "Bangalore": "080",
    "Bengaluru": "080",
    "Mumbai": "022",
    "Delhi": "011",
    "Hyderabad": "040",
    "Kolkata": "033",
    "Pune": "020",
    "Ahmedabad": "079",
    "Jaipur": "0141",
    "Lucknow": "0522",
    "Kochi": "0484",
    "Thiruvananthapuram": "0471",
    "Nagpur": "0712",
    "Indore": "0731",
    "Bhopal": "0755",
    "Patna": "0612",
    "Chandigarh": "0172",
    "Visakhapatnam": "0891",
    "Vijayawada": "0866"
}
