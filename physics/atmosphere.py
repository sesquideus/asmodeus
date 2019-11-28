import sys
import math
import numba
import numpy as np

from physics import constants


def drag_coefficient_smooth_sphere(reynolds):
    if reynolds == 0:
        return 0
    a  = reynolds / 5
    b = reynolds / 263000
    c = reynolds / 1000000

    return 24 / reynolds \
        + 2.6 * a / (1 + a)**1.52 \
        + 0.411 * b**-7.94 / (1 + b**-8) \
        + 0.25 * c / (1 + c)


def Reynolds_number(length, speed, density):
    return length * speed * density / constants.AIR_VISCOSITY


def air_mass_Kasten_Young(altitude, observer_elevation = 0):
    if altitude >= 0:
        return (air_density(observer_elevation) / air_density(0)) / (math.sin(math.radians(altitude)) + 0.50572 * ((altitude + 6.07995) ** (-1.6364)))
    else:
        return np.inf


def air_mass_pickering_2002(altitude, observer_elevation = 0):
    if altitude >= 0:
        return (air_density(observer_elevation) / air_density(0)) / (math.sin(math.radians(altitude + (244 / (165 + 47 * altitude**1.1)))))
    else:
        return np.inf

air_mass = air_mass_Kasten_Young


def attenuate(flux, air_mass):
    return flux * math.exp(constants.ATTENUATION_ONE_AIR_MASS * air_mass)


#@numba.njit
def air_density_MSIS(altitude):
    if altitude >= 500000:
        return 0

    if altitude < 0:
        return 1

    i = int(altitude // 500)
    f = (altitude - 500 * i) / 500

    logs = [
        -6.710545109694432,
        -6.764521110896229,
        -6.817914574982348,
        -6.869496566865046,
        -6.920334061188997,
        -6.970482108890442,
        -7.020252310209283,
        -7.069803730936536,
        -7.119464452670684,
        -7.169379817114629,
        -7.219730044002962,
        -7.270879546600776,
        -7.322664845918301,
        -7.3755214132876805,
        -7.429473343914552,
        -7.4847207052526725,
        -7.541125255506222,
        -7.599104077600703,
        -7.658531572378719,
        -7.719460795666217,
        -7.781944834837657,
        -7.846036028747907,
        -7.911784925164299,
        -7.9789469720742545,
        -8.047502111008802,
        -8.117746155633636,
        -8.189329329331624,
        -8.261776079551732,
        -8.335705315370861,
        -8.411032995587847,
        -8.487149070067861,
        -8.5648090453579,
        -8.642756414391583,
        -8.721760357157512,
        -8.80088324259848,
        -8.881036624833582,
        -8.961139286342684,
        -9.04144183551437,
        -9.122329494653469,
        -9.202372202327005,
        -9.282481049753866,
        -9.36244315018614,
        -9.442020254312679,
        -9.521359309792402,
        -9.600424378046045,
        -9.679384461727219,
        -9.758002885794147,
        -9.836576847253502,
        -9.914953030645407,
        -9.993193465620621,
        -10.071196396962238,
        -10.14913236919685,
        -10.227004077997124,
        -10.304861042741038,
        -10.382491563979162,
        -10.460008135564248,
        -10.537611392646612,
        -10.61520611868151,
        -10.692705201846808,
        -10.77003619251547,
        -10.847149481206415,
        -10.92458339877641,
        -11.001300161033674,
        -11.078549013367644,
        -11.155950566022499,
        -11.23302357983741,
        -11.30916862745621,
        -11.38541214467127,
        -11.46128223181839,
        -11.536501201498934,
        -11.61120003423857,
        -11.68537590196892,
        -11.75908179059351,
        -11.832167006329776,
        -11.904783569672176,
        -11.97702654856335,
        -12.04855620765519,
        -12.119711479882131,
        -12.190396166145167,
        -12.260528831326232,
        -12.33027624898948,
        -12.399414705607594,
        -12.467957025160814,
        -12.536244769602908,
        -12.603867247334119,
        -12.671287758044112,
        -12.738121905747791,
        -12.804273348781166,
        -12.870438024664667,
        -12.93588381046171,
        -13.001031092236804,
        -13.065510565811547,
        -13.12989164382512,
        -13.1938593791094,
        -13.257610526812355,
        -13.320814316128168,
        -13.383728141538736,
        -13.446018110314927,
        -13.508761422795267,
        -13.570996980913872,
        -13.633189001170319,
        -13.695064404888408,
        -13.756298698332428,
        -13.81781320702695,
        -13.879196109650406,
        -13.94050704813896,
        -14.00171966148542,
        -14.062818736277782,
        -14.123939703560845,
        -14.184981305849062,
        -14.246139639735988,
        -14.307350881819184,
        -14.368548030539575,
        -14.42984655809993,
        -14.491210824920499,
        -14.55281863430999,
        -14.614462797421195,
        -14.676366582950328,
        -14.738574174125858,
        -14.80061560583879,
        -14.863334679800278,
        -14.92599301920287,
        -14.989277520233145,
        -15.052695496496323,
        -15.116361437266697,
        -15.180434893347972,
        -15.244712420095441,
        -15.309390129764102,
        -15.374730754237756,
        -15.440062108208423,
        -15.506158525823917,
        -15.572868600474997,
        -15.639380081110563,
        -15.706648471172608,
        -15.774505946568242,
        -15.842739228197177,
        -15.911894820374423,
        -15.980945812811086,
        -16.050437002484504,
        -16.121100159978617,
        -16.191957499556775,
        -16.263352663615457,
        -16.33538139278837,
        -16.407913335540524,
        -16.48107614746033,
        -16.554741876550057,
        -16.628088288420418,
        -16.702029746544948,
        -16.77626186262302,
        -16.850607555040543,
        -16.925531977920393,
        -17.00070985647309,
        -17.076511309133146,
        -17.153169918822442,
        -17.23040126675843,
        -17.308494335257137,
        -17.38714045202797,
        -17.467094227334513,
        -17.54813293502613,
        -17.629953235053556,
        -17.713137683108688,
        -17.796883641527213,
        -17.881850923776778,
        -17.96833204994535,
        -18.056037630364457,
        -18.14456530787205,
        -18.234201177009748,
        -18.32537056414804,
        -18.417685234972566,
        -18.510496048274728,
        -18.604723781644662,
        -18.70013013147767,
        -18.796392893911182,
        -18.89388950414705,
        -18.992141406255712,
        -19.091479520848548,
        -19.191573273137163,
        -19.29247623593997,
        -19.39433579321609,
        -19.496846843790646,
        -19.59996093568793,
        -19.703696755618754,
        -19.807775425243026,
        -19.912335620730083,
        -20.016708969476547,
        -20.121138054773635,
        -20.225525452729077,
        -20.329198773790615,
        -20.432837538826604,
        -20.535127894831017,
        -20.63708814070536,
        -20.738582541058303,
        -20.83878892820195,
        -20.937821371074087,
        -21.03578719941184,
        -21.1324378069859,
        -21.22777809865581,
        -21.321648441061935,
        -21.414015892906637,
        -21.50480716826895,
        -21.593627636932165,
        -21.681160118675642,
        -21.76682191986644,
        -21.850895074685013,
        -21.933927629423145,
        -22.015705622594677,
        -22.09644655892092,
        -22.17655506689058,
        -22.255742708244384,
        -22.334204875506778,
        -22.412288228723355,
        -22.489942525807002,
        -22.567161060594994,
        -22.64467851440134,
        -22.72204947560879,
        -22.79871535735671,
        -22.876569227224703,
        -22.95353026836083,
        -23.031366110628568,
        -23.10944995381677,
        -23.187899381894855,
        -23.266776651050463,
        -23.345918462536392,
        -23.425433374890467,
        -23.50501640097858,
        -23.584642058001325,
        -23.664131209059562,
        -23.7434957421008,
        -23.822360623495555,
        -23.900999718483437,
        -23.97932445294233,
        -24.056991503493553,
        -24.13421057006345,
        -24.210347957765737,
        -24.28604141426462,
        -24.360692009471432,
        -24.434390900007667,
        -24.50689562760616,
        -24.578436030781774,
        -24.64837408192321,
        -24.717041344246816,
        -24.78436906538871,
        -24.849720453086746,
        -24.913680867919247,
        -24.974966209944718,
        -25.03502041863496,
        -25.090206834202252,
        -25.14611446614055,
        -25.200042808166103,
        -25.253328550447698,
        -25.304719496317187,
        -25.356012790704735,
        -25.405857169903086,
        -25.454679749508752,
        -25.50267036954584,
        -25.549706329867032,
        -25.595923388100765,
        -25.64123079620136,
        -25.685825507811103,
        -25.729809513139415,
        -25.77284988118124,
        -25.815382372910552,
        -25.857086231613046,
        -25.898127399567528,
        -25.93871372567215,
        -25.978523714034,
        -26.017989667984317,
        -26.05679595925019,
        -26.095014481580332,
        -26.13273825286061,
        -26.16985122016355,
        -26.206708687621138,
        -26.24297828427454,
        -26.278800735142408,
        -26.31407683294345,
        -26.34925428416259,
        -26.383701507099246,
        -26.417890373817848,
        -26.451750924242983,
        -26.485207225776144,
        -26.518177245013714,
        -26.550912298824997,
        -26.583000613376498,
        -26.615066060941448,
        -26.647071735580578,
        -26.67820560937202,
        -26.709543857367095,
        -26.74025334128548,
        -26.770666016384695,
        -26.80072409722137,
        -26.830814863075194,
        -26.860450038403798,
        -26.890036605954442,
        -26.919052181128016,
        -26.947924271222103,
        -26.976614763685035,
        -27.005082685062053,
        -27.03328412017326,
        -27.06173792259099,
        -27.089278389527838,
        -27.11700060126604,
        -27.144283287691646,
        -27.171699335029672,
        -27.19858955959057,
        -27.225556007820384,
        -27.251899983159987,
        -27.278253796820835,
        -27.304599215160838,
        -27.33091652347821,
        -27.356424283025422,
        -27.38259975743007,
        -27.40787756461434,
        -27.433810946640843,
        -27.458749894988095,
        -27.484326736777746,
        -27.5088034832043,
        -27.533894405197824,
        -27.558700454348923,
        -27.58318378651439,
        -27.607304589311234,
        -27.631721361042942,
        -27.655928751634733,
        -27.679896283710686,
        -27.703806885654203,
        -27.727532016309393,
        -27.751269688524722,
        -27.774776019573686,
        -27.79813883898023,
        -27.821455492833053,
        -27.844585692462434,
        -27.867756620762226,
        -27.890698991970734,
        -27.91351666169303,
        -27.936324197137733,
        -27.958969781608886,
        -27.981430018288634,
        -28.003970632360033,
        -28.026288399060267,
        -28.048508199264038,
        -28.07061193876609,
        -28.09273916558751,
        -28.114718072306285,
        -28.136693374453746,
        -28.15848438084756,
        -28.180067952514737,
        -28.201773688274887,
        -28.22323757791005,
        -28.244802741107755,
        -28.26608808541197,
        -28.28745071355333,
        -28.308688725640106,
        -28.32978403527413,
        -28.35092303379731,
        -28.371889032699904,
        -28.392875494498284,
        -28.41365546299003,
        -28.43442969074603,
        -28.4551885589269,
        -28.47592185171603,
        -28.49638111913416,
        -28.51702515519783,
        -28.537361516949534,
        -28.557614740798602,
        -28.578028820464763,
        -28.59834201891548,
        -28.61853935709107,
        -28.638605106249095,
        -28.658802223836066,
        -28.678560134412656,
        -28.698716301961937,
        -28.71839677267067,
        -28.738472353263862,
        -28.758032879118357,
        -28.777668853635216,
        -28.797377056683178,
        -28.817154002126152,
        -28.83666197735518,
        -28.85621755670611,
        -28.875468752820204,
        -28.89509784432419,
        -28.914397943041752,
        -28.93370989319364,
        -28.952651963722715,
        -28.97195977532764,
        -28.99125794272915,
        -29.010141273300437,
        -29.02938805828271,
        -29.048187140715527,
        -29.067346410654004,
        -29.08602267505823,
        -29.105054391356447,
        -29.1240102157194,
        -29.14242528809128,
        -29.16118584746814,
        -29.179834406546213,
        -29.19883735367183,
        -29.21723090224344,
        -29.235969123089795,
        -29.254050981882116,
        -29.272465824497736,
        -29.291226145416303,
        -29.309273344363007,
        -29.327652240065024,
        -29.346375253954196,
        -29.364323015585036,
        -29.382598795523773,
        -29.40062778051547,
        -29.418987786917906,
        -29.43708236986746,
        -29.454890639074836,
        -29.47302180159335,
        -29.490845316070732,
        -29.50899228197567,
        -29.526808655580652,
        -29.54494821913081,
        -29.562732545584048,
        -29.580838889814878,
        -29.598563565110975,
        -29.615880015122436,
        -29.633501616472255,
        -29.651439317158925,
        -29.668936910779887,
        -29.686746130991068,
        -29.704083050644346,
        -29.721725849887093,
        -29.73886213213008,
        -29.756297193952182,
        -29.774041639251255,
        -29.79123896763567,
        -29.808737226876726,
        -29.826547136629188,
        -29.843765504922803,
        -29.860355747183,
        -29.878171502034494,
        -29.895347496805503,
        -29.912823669740064,
        -29.929614187653055,
        -29.94659013648089,
        -29.963653130274892,
        -29.980697816456445,
        -29.997718154389837,
        -30.014707810359635,
        -30.031660149397982,
        -30.048568227392277,
        -30.065538880183418,
        -30.082338262722992,
        -30.09918864971227,
        -30.11596776651657,
        -30.13278912279196,
        -30.149525915147485,
        -30.166168982153295,
        -30.182965407055217,
        -30.199526789592863,
        -30.216234407071696,
        -30.2328211971881,
        -30.249413445100224,
        -30.26586732477234,
        -30.282454716611863,
        -30.298889527397925,
        -30.315452451432126,
        -30.33184747194144,
        -30.34821297494804,
        -30.36469686466973,
        -30.38098766013205,
        -30.39723023120429,
        -30.41357936920582,
        -30.429871681357255,
        -30.44609988978928,
        -30.462256417601136,
        -30.478505813022338,
        -30.494673049125332,
        -30.510749713726234,
        -30.526908054512823,
        -30.542963863752856,
        -30.559094741008725,
        -30.5751101563307,
        -30.591193214083987,
        -30.60714685984362,
        -30.62315985397241,
        -30.63902842035815,
        -30.654947123853322,
        -30.670705277011724,
        -30.686715730655223,
        -30.70255510289882,
        -30.718210999971372,
        -30.734115907811038,
        -30.749825387072534,
        -30.765555792363,
        -30.781304149331138,
        -30.796830219860055,
        -30.812601156053052,
        -30.828135449015235,
        -30.843914869119203,
        -30.85944235364028,
        -30.87495837139212,
        -30.89045855255287,
        -30.905938331680375,
        -30.921392942501818,
        -30.936817412827452,
        -30.95248352957185,
        -30.967836238661434,
        -30.98314265994411,
        -30.998396949115193,
        -31.01388754090598,
        -31.02932269447868,
        -31.044392298522414,
        -31.059692474591458,
        -31.074917252123818,
        -31.090377411764237,
        -31.105434559921964,
        -31.120721896182108,
        -31.135913733929467,
        -31.15100203358067,
        -31.16597848777023,
        -31.181182650730662,
        -31.19626800959721,
        -31.211225553416828,
        -31.22604599457086,
        -31.241089389618196,
        -31.255987244298833,
        -31.271110405873053,
        -31.286079021566973,
        -31.300882564206724,
        -31.315908548772946,
        -31.33075931337736,
        -31.34542352727357,
        -31.360305984677524,
        -31.374990536360446,
        -31.38989394186302,
        -31.40458737820968,
        -31.41949993526524,
        -31.434189716444614,
        -31.44864344593521,
        -31.46330915333784,
        -31.47819314903708,
        -31.492826405196077,
        -31.507194468463,
        -31.521771986081156,
        -31.536565155258984,
        -31.55107629305396,
        -31.565289730304013,
        -31.58022691248441,
        -31.594337415744246,
        -31.60864987845469,
        -31.62317016583598,
        -31.637904402380656,
        -31.652301107293642,
        -31.666342337701188,
        -31.680583535378755,
        -31.695030478354575,
        -31.70968919876564,
        -31.723966657236943,
        -31.73784319966176,
        -31.752531346223417,
        -31.766187672670902,
        -31.78066699393574,
        -31.79471575628544,
        -31.808964702026962,
        -31.823419618626037,
        -31.837415181959273,
        -31.8516094047249,
        -31.865317638578095,
        -31.879216402968908,
        -31.893311069000095,
        -31.907607238144433,
        -31.921380562076607,
        -31.93534624293858,
        -31.949509729798443,
        -31.96387670659598,
        -31.977680606765137,
        -31.991677724866236,
        -32.00507958095325,
        -32.01946831840535,
        -32.03325045791995,
        -32.046397730283985,
        -32.06055873327348,
        -32.074072452440205,
        -32.087771296798365,
        -32.101660408959034,
        -32.11574514884077,
        -32.12913222962323,
        -32.1427009588293,
        -32.156456333897786,
        -32.170403561378635,
        -32.18359885179747,
        -32.19793258979955,
        -32.21149868932627,
        -32.22525136187831,
        -32.23839372547184,
        -32.25201585226361,
        -32.265517131298466,
        -32.27899442424195,
        -32.292550035586025,
        -32.305970196524555,
        -32.31946422111046,
        -32.33292249087641,
        -32.346341045417624,
        -32.35971578820214,
        -32.3731571569898,
        -32.38643296524718,
        -32.40024081392315,
        -32.41352531719956,
        -32.42686766309335,
        -32.44014515883771,
        -32.45347704374669,
        -32.46673718299761,
        -32.479920286839956,
        -32.49315020172558,
        -32.5064264607647,
        -32.51961578411578,
        -32.53284684916753,
        -32.54598265995652,
        -32.55915518851306,
        -32.57222363530947,
        -32.585323336684645,
        -32.598453252724156,
        -32.61146673886174,
        -32.62465181120898,
        -32.63771419079218,
        -32.65064670186294,
        -32.66374865649962,
        -32.67671380184021,
        -32.68969185906336,
        -32.70268111186258,
        -32.71567977037359,
        -32.728522343046464,
        -32.741531995452064,
        -32.754377280088924,
        -32.76721963300015,
        -32.780056779760834,
        -32.793060864184035,
        -32.805882678549665,
        -32.81869196238952,
        -32.83148608230908,
        -32.844262310121465,
        -32.85701782089696,
        -32.869749691064925,
        -32.8826457544846,
        -32.89532360388931,
        -32.90796845674039,
        -32.920775251816096,
        -32.93334650387413,
        -32.946077806480886,
        -32.9587672931674,
        -32.97141125889849,
        -32.984005883818895,
        -32.99654723217004,
        -33.009247865704886,
        -33.021892464087195,
        -33.03447680059989,
        -33.04699652594482,
        -33.059447167823606,
        -33.07205478467818,
        -33.08458976774788,
        -33.0970473269027,
        -33.109662036607865,
        -33.12195282875597,
        -33.13439656624441,
        -33.146997103560224,
        -33.159506648727756,
        -33.17191972768327,
        -33.18423073210538,
        -33.19669518846712,
        -33.209052385279186,
        -33.22129634979115,
        -33.23369208921634,
        -33.245968876884255,
        -33.258398259382346,
        -33.27070266517823,
        -33.28287549772439,
        -33.29519833599239,
        -33.307674923196494,
        -33.31971795316671,
        -33.33220696473748,
        -33.34424804941275,
        -33.356435890711865,
        -33.368774110155904,
        -33.38095224661073,
        -33.39328052034372,
        -33.40544067018419,
        -33.417424619273085,
        -33.42955392713056,
        -33.44183216334327,
        -33.453925021492616,
        -33.46582385302315,
        -33.4782121738801,
        -33.49005487585604,
        -33.50239418277871,
        -33.51416951955307,
        -33.52644847483959,
        -33.53851222926035,
        -33.55035106527733,
        -33.562331740216784,
        -33.57445769402595,
        -33.586346616420656,
        -33.5983785876933,
        -33.610557092171256,
        -33.62248566303653,
        -33.63415346790421,
        -33.64636860349986,
        -33.65832011604574,
        -33.669996645707585,
        -33.68181112912134,
        -33.693766865041496,
        -33.705867271975585,
        -33.71767585004028,
        -33.72962553859443,
        -33.7412691990265,
        -33.75305003305765,
        -33.764971311333284,
        -33.77656967841924,
        -33.788776402757954,
        -33.80017795144682,
        -33.812194438264505,
        -33.823867722569226,
        -33.83567888349757,
        -33.847631217021416,
        -33.85922116787021,
        -33.87094702233503,
        -33.882812005478456,
        -33.89429438633202,
        -33.90591014523567,
        -33.91766241725057,
        -33.9295544492885,
        -33.9410393991554,
        -33.95265778710926,
        -33.964412750340706,
        -33.97573789969776,
        -33.98776898151186,
        -33.99936331429278,
        -34.01109365407827,
        -34.02236639285079,
        -34.03376765646626,
        -34.04530040947981,
        -34.056967720215184,
        -34.06877276566495,
        -34.08008652556522,
        -34.091529752787565,
        -34.10310544474545,
        -34.11481670416636,
        -34.12666674408385,
        -34.13798887635363,
        -34.1494406687324,
        -34.16102512537004,
        -34.17205211511895,
        -34.18390307291858,
        -34.19518669052061,
        -34.20659908257235,
        -34.21814322231922,
        -34.229822187183366,
        -34.24089649748246,
        -34.252094822792486,
        -34.26341997214954,
        -34.27487485112431,
        -34.2864624662967,
        -34.298185929992755,
        -34.309253236632436,
        -34.3204444005937,
        -34.33176222552636,
        -34.34320961136671,
        -34.35478955879767,
        -34.36566377720204,
        -34.377508247314566,
        -34.38863373648097,
        -34.399884396044065,
        -34.411263074611725,
        -34.42277271915438,
        -34.43351588425319,
        -34.445286051823345,
        -34.45627517339894,
        -34.46738639882401,
        -34.47862247209094,
        -34.48998623074125,
        -34.501480610166986,
        -34.512134463964266,
        -34.523887782416935,
        -34.534784373641145,
        -34.546103170297144,
        -34.55724591119435,
        -34.56841120004037,
        -34.57959838943094,
        -34.59080680300507,
        -34.60192920991595,
        -34.61306899949254,
        -34.62422535674317,
        -34.63539743351511,
        -34.64647297036606,
        -34.65755993090065,
        -34.6686573157652,
        -34.67976408821166,
        -34.69087917312064,
        -34.702001456013654,
        -34.71312978205546,
        -34.72414258189087,
        -34.735278015278475,
        -34.746292690339196,
        -34.75730560867415,
        -34.76831535331375,
        -34.77944766309311,
        -34.79044802983943,
        -34.801440704387176,
        -34.81518887510423,
        -34.82619183624504,
        -34.83718243072544,
        -34.84815889434181,
        -34.85911940960203,
        -34.8700621048446,
        -34.88098505338383,
        -34.89188627268492,
        -34.90290763952587,
        -34.91376079576526,
        -34.924733036630805,
        -34.93567827235836,
        -34.946594268602446,
        -34.95747872980087,
        -34.96832929854794,
        -34.97929889483425,
        -34.99023308686984,
        -35.00097059726494,
        -35.01198515510537,
        -35.022797815924626,
        -35.03356464097905,
        -35.04444865343588,
        -35.05528480181217,
        -35.0662396598297,
        -35.076973215472805,
        -35.08782323149688,
        -35.09861720816241,
        -35.10952896725703,
        -35.12038220073772,
        -35.13117367237049,
        -35.14190007282304,
        -35.15274277759619,
        -35.163517542806574,
        -35.17422086534234,
        -35.18503998957178,
        -35.19578452885476,
        -35.206645768286364,
        -35.21742912932018,
        -35.22813077723193,
        -35.2389481904076,
        -35.24968029705989,
        -35.26032304999233,
        -35.271080290671826,
        -35.28174427045459,
        -35.29252319759956,
        -35.30320477747559,
        -35.31400168650624,
        -35.324696975622984,
        -35.335286088465786,
        -35.3459885317586,
        -35.35680675761732,
        -35.36751422977698,
        -35.37810608564871,
        -35.38881133100777,
        -35.39939592941438,
        -35.41009376114211,
        -35.42066570006751,
        -35.43135060016753,
        -35.44190414025856,
        -35.452570246586255,
        -35.46335134637254,
        -35.47399513667036,
        -35.48449593747565,
        -35.49510817632203,
        -35.50583424383849,
        -35.516410757025895,
        -35.52683169301415,
        -35.5376338504418,
        -35.54800512244411,
        -35.558762363123606,
        -35.56935627318697,
        -35.57978037095848,
        -35.59031427619286,
        -35.60096032696524,
        -35.611428581909266,
        -35.622007581540494,
        -35.632699694092665,
        -35.64320556890036,
        -35.65382299004222,
        -35.66424613774868,
        -35.67477907279736,
        -35.68542413261735,
        -35.69586561333777,
        -35.70641726998923,
        -35.716756618962364,
        -35.727203987901156,
        -35.737761657725585,
        -35.74843198237212,
        -35.758878581166506,
        -35.76909317457622,
        -35.77975902487052,
        -35.79019027383676,
        -35.80073148177497,
        -35.811028039989914,
        -35.82143172127109,
        -35.83194477804109,
        -35.84256953451883,
        -35.852936158271376,
        -35.86341137564385,
        -35.87361747444166,
        -35.884312763558405,
        -35.8947355562345,
        -35.9052681287344,
        -35.91551654322576,
        -35.92587107620135,
        -35.93633394830929,
        -35.94690745063975,
        -35.95718080994881,
        -35.96756080765153,
        -35.978049680821464,
        -35.988223571035846,
        -35.998502034116456,
        -36.008887242123684,
        -36.01938143550182,
        -36.029542777627285,
        -36.04025716583969,
        -36.05018056707342,
        -36.06066141033693,
        -36.07125326620866,
        -36.08149067530188,
        -36.09183397390868,
        -36.10180793453063,
        -36.11236465445109,
        -36.122546560596206,
        -36.13283320530648,
        -36.143226765833745,
        -36.153729488032894,
        -36.163835688247744,
        -36.17404506737931,
        -36.18435975398114,
        -36.19478194316112,
        -36.20478465883318,
        -36.21542305703824,
        -36.22563545431337,
        -36.23595322165279,
        -36.24582713621179,
        -36.25635646596449,
        -36.26643493873222,
        -36.27661602214931,
        -36.286901827118676,
        -36.29729453035894,
        -36.307210038835244,
        -36.317817091730966,
        -36.32793923829148,
        -36.33816489130323,
        -36.348496189515735,
        -36.35831824515119,
        -36.36886097846041,
        -36.37888612507979,
        -36.38901279389771,
        -36.39924306214853,
        -36.40957907147919,
        -36.41936707784536,
        -36.42991430811902,
        -36.439904401194106,
        -36.44999530417607,
        -36.46018907236561,
        -36.470487824566185,
        -36.4808937457273,
        -36.49070461629156,
        -36.500612694516256,
        -36.511338574963425,
        -36.521454268158216,
        -36.53093992848346,
        -36.541256895454396,
        -36.55168141279028,
        -36.56145960277191,
        -36.57133435069167,
        -36.582078889974646,
        -36.59216040227123,
        -36.60234458743423,
        -36.61183832962648,
        -36.62222595798806,
        -36.63191126372252,
        -36.64251062915957,
        -36.65239538839211,
        -36.66237883237629,
        -36.67246295144292,
        -36.682649796749914,
        -36.69294148278646,
        -36.702469489038116,
        -36.71296827313633,
        -36.72268995818723,
        -36.73250708299265,
        -36.742421540049826,
        -36.75243527871033,
        -36.76255030748044,
        -36.77276869643912,
        -36.78309257978076,
        -36.7925713237353,
        -36.80310277578764,
        -36.81277403105282,
        -36.822539733664144,
        -36.83240174653326,
        -36.84276246882036,
        -36.85272581798378,
        -36.86268727461948,
        -36.8726457779445,
        -36.88260023592133,
        -36.89255469389816,
    ]

    return math.exp(logs[i] + (logs[i+1] - logs[i]) * f) * 1000


air_density = air_density_MSIS
