# encoding: utf-8


#The information in this module was gleaned from DataLinkHandlers.cs
#https://github.com/richardbunt/Telemachus/blob/master/Telemachus/src/DataLinkHandlers.cs

#Actions are sent to server, result in one action per message
mj_actions = ['mj.smartassoff',    # Smart ASS Off
              #'mj.smartasson',     # Why does this not exist?
              'mj.node',           # Node
              'mj.prograde',       # Prograde
              'mj.retrograde',     # Retrograde
              'mj.normalplus',     # Normal Plus
              'mj.normalminus',    # Normal Minus
              'mj.radialplus',     # Radial Plus
              'mj.radialminus',    # Radial Minus
              'mj.targetplus',     # Target Plus
              'mj.targetminus',    # Target Minus
              'mj.relativeplus',   # Relative Plus
              'mj.relativeminus',  # Relative Minus
              'mj.parallelplus',   # Parallel Plus
              'mj.parallelminus',  # Parallel Minus
              'mj.surface',        # Surface [float heading, float pitch]
              'mj.surface2',       # Surface [double heading, double pitch]
              ]

#FlyByWire Stuff
vessel_actions = ['v.setYaw',    # Yaw [float yaw]
                  'v.setPitch',  # Pitch [float pitch]
                  'v.setRoll',   # Roll [float roll]
                  'v.setFbW',    # Set Fly by Wire On or Off [bool state]
                  'v.setPitchYawRollXYZ',  # Set pitch, yaw, roll, X, Y and Z [float pitch, yaw, roll, x, y, z]
                  ]

flight_actions = ['f.stage',         # Stage
                  'f.setThrottle',   # Set Throttle [float magnitude]
                  'f.throttle',      # Throttle ; what does this do?
                  'f.throttleUp',    # Throttle Up
                  'f.throttleZero',  # Throttle Zero
                  'f.throttleFull',  # Throttle Full
                  'f.throttleDown',  # Throttle Down
                  'f.rcs',           # RCS [optional bool on/off]
                  'f.sas',           # SAS [optional bool on/off]
                  'f.light',         # Light [optional bool on/off]
                  'f.gear',          # Gear [optional bool on/off]
                  'f.brake',         # Brake [optional bool on/off]
                  'f.abort',         # Abort [optional bool on/off]
                  'f.ag1',           # Action Group 1 [optional bool on/off]
                  'f.ag2',           # Action Group 2 [optional bool on/off]
                  'f.ag3',           # Action Group 3 [optional bool on/off]
                  'f.ag4',           # Action Group 4 [optional bool on/off]
                  'f.ag5',           # Action Group 5 [optional bool on/off]
                  'f.ag6',           # Action Group 6 [optional bool on/off]
                  'f.ag7',           # Action Group 7 [optional bool on/off]
                  'f.ag8',           # Action Group 8 [optional bool on/off]
                  'f.ag9',           # Action Group 9 [optional bool on/off]
                  'f.ag10',          # Action Group 10 [optional bool on/off]
                  'f.rcsValue',      # Query RCS value
                  'f.sasValue',      # Query SAS value
                  'f.lightValue',    # Query light value
                  'f.brakeValue',    # Query brake value
                  'f.gearValue',     # Query gear value
                  ]

time_warp_actions = ['t.timeWarp',       # Time Warp [int rate]
                     ]

#MapView here refers to the in-game orbital map, not the google maps hook
mapview_actions = ['m.toggleMapView',  # Toggle Map View
                   'm.enterMapView',   # Enter Map View
                   'm.exitMapView',    # Exit Map View
                   ]

#Plotables are things you can subscribe to; will be sent at each pulse
target_plotables = ['tar.o.sma',           # Target Semimajor Axis
                    'tar.o.lan',           # Target Longitude of Ascending Node
                    'tar.o.maae',          # Target Mean Anomaly at Epoch
                    'tar.name',            # Target Name
                    'tar.type',            # Target Type
                    'tar.distance',        # Target Distance
                    'tar.o.velocity',      # Target Velocity
                    'tar.o.PeA',           # Target Periapsis
                    'tar.o.ApA',           # Target Apoapsis
                    'tar.o.timeToAp',      # Target Time to Apoapsis
                    'tar.o.timeToPe',      # Target Time to Periapsis
                    'tar.o.inclination',   # Target Inclination
                    'tar.o.eccentricity',  # Target Eccentricity
                    'tar.o.period',        # Target Orbital Period
                    'tar.o.relativeVelocity',  # Target Relative Velocity
                    #Sends improperly encoded text back!
                    #'tar.o.trueAnomaly',       # Target True Anomaly
                    'tar.o.orbitingBody',      # Target Orbiting Body
                    'tar.o.argumentOfPeriapsis',     # Target Argument of Periapsis
                    'tar.o.timeToTransition1',       # Target Time to Transition 1
                    'tar.o.timeToTransition2',       # Target Time to Transition 2
                    'tar.o.timeOfPeriapsisPassage',  # Target Time of Periapsis Passage
                    ]

docking_plotables = ['dock.ax',  # Docking x Angle
                     'dock.ay',  # Relative Pitch Angle
                     'dock.az',  # Docking z Angle
                     'dock.x',   # Target x Distance
                     'dock.y',   # Target y Distance
                     ]

#In my tests, none of these can be used. Breaks the connection
#body_plotables = ['b.name',                      # Body Name
                  #'b.maxAtmosphere',             # Body Max Atmosphere
                  #'b.radius',                    # Body Radius
                  #'b.number',                    # Number of Bodies
                  #'b.o.gravParameter',           # Body Gravitational Parameter
                  #'b.o.relativeVelocity',        # Relative Velocity
                  #'b.o.PeA',                     # Periapsis
                  #'b.o.ApA',                     # Apoapsis
                  #'b.o.timeToAp',                # Time to Apoapsis
                  #'b.o.timeToPe',                # Time to Periapsis
                  #'b.o.inclination',             # Inclination
                  #'b.o.eccentricity',            # Eccentricity
                  #'b.o.period',                  # Orbital Period
                  #'b.o.argumentOfPeriapsis',     # Argument of Periapsis
                  #'b.o.timeToTransition1',       # Time to Transition 1
                  #'b.o.timeToTransition2',       # Time to Transition 2
                  #'b.o.sma',                     # Semimajor Axis
                  #'b.o.lan',                     # Longitude of Ascending Node
                  #'b.o.maae',                    # Mean Anomaly at Epoch
                  #'b.o.timeOfPeriapsisPassage',  # Time of Periapsis Passage
                  #'b.o.trueAnomaly',             # True Anomaly
                  #'b.o.phaseAngle',              # Phase Angle
                  #]

navball_plotables = ['n.heading',     # Heading
                     'n.pitch',       # Pitch
                     'n.roll',        # Roll
                     'n.rawheading',  # Raw Heading
                     'n.rawpitch',    # Raw Pitch
                     'n.rawroll',     # Raw Roll
                     ]

vessel_plotables = ['v.altitude',            # Altitude
                    'v.heightFromTerrain',   # Height from Terrain
                    'v.terrainHeight',       # Terrain Height
                    'v.missionTime',         # Mission Time
                    'v.surfaceVelocity',     # Surface Velocity
                    'v.surfaceVelocityx',    # Surface Velocity x
                    'v.surfaceVelocityy',    # Surface Velocity y
                    'v.surfaceVelocityz',    # Surface Velocity z
                    'v.angularVelocity',     # Angular Velocity
                    'v.orbitalVelocity',     # Orbital Velocity
                    'v.surfaceSpeed',        # Surface Speed
                    'v.verticalSpeed',       # Vertical Speed
                    'v.geeForce',            # G-Force
                    'v.atmosphericDensity',  # Atmospheric Density
                    'v.long',                # Longitude
                    'v.lat',                 # Latitude
                    'v.dynamicPressure',     # Dynamic Pressure
                    'v.name',                # Name
                    'v.body',                # Body Name
                    'v.angleToPrograde',     # Angle to Prograde
                    ]

orbit_plotables = ['o.relativeVelocity',        # Relative Velocity
                   'o.PeA',                     # Periapsis
                   'o.ApA',                     # Apoapsis
                   'o.timeToAp',                # Time to Apoapsis
                   'o.timeToPe',                # Time to Periapsis
                   'o.inclination',             # Inclination
                   'o.eccentricity',            # Eccentricity
                   'o.epoch',                   # Epoch
                   'o.period',                  # Orbital Period
                   'o.argumentOfPeriapsis',     # Argument of Periapsis
                   'o.timeToTransition1',       # Time to Transition 1
                   'o.timeToTransition2',       # Time to Transition 2
                   'o.sma',                     # Semimajor Axis
                   'o.lan',                     # Longitude of Ascending Node
                   'o.maae',                    # Mean Anomaly at Epoch
                   'o.timeOfPeriapsisPassage',  # Time of Periapsis Passage
                   'o.trueAnomaly',             # True Anomaly'
                   ]

orbit_plots_names = {'o.relativeVelocity': 'Relative Velocity',
                     'o.PeA': 'Periapsis',
                     'o.ApA': 'Apoapsis',
                     'o.timeToAp': 'Time to Apoapsis',
                     'o.timeToPe': 'Time to Periapsis',
                     'o.inclination': 'Inclination',
                     'o.eccentricity': 'Eccentricity',
                     'o.epoch': 'Epoch',
                     'o.period': 'Orbital Period',
                     'o.argumentOfPeriapsis': 'Argument of Periapsis',
                     'o.timeToTransition1': 'Time to Transition 1',
                     'o.timeToTransition2': 'Time to Transition 2',
                     'o.sma': 'Semimajor Axis',
                     'o.lan': 'Longitude of Ascending Node',
                     'o.maae': 'Mean Anomaly at Epoch',
                     'o.timeOfPeriapsisPassage': 'Time of Periapsis Passage',
                     'o.trueAnomaly': 'True Anomaly',
                     }

sensor_plotables = [#'s.sensor',       # Sensor Information [string sensor type]
                    's.sensor.temp',  # Temperature sensor information
                    's.sensor.pres',  # Pressure sensor information
                    's.sensor.grav',  # Gravity sensor information
                    's.sensor.acc',   # Acceleration sensor information
                    ]

paused_plotables = ['p.paused',  # Paused
                    ]

api_plotables = ['a.version',  # Telemachus Version
                 ]

time_warp_plotables = ['t.universalTime',  # Universal Time
                       ]

#These consitute the safe set of plotable values to work with
plotables = target_plotables + docking_plotables + \
            navball_plotables + vessel_plotables + orbit_plotables + \
            sensor_plotables + api_plotables + time_warp_plotables\


#Plain API Entries: how exactly do these work?
resources = ['r.resource',         # Resource Information [string resource type]
             'r.resourceCurrent',  # Resource Information for Current Stage [string resource type]
             'r.resourceMax',      # Max Resource Information [string resource type]
             ]

apis = ['a.api',        # API Listing
        'a.ip',         # IP Addresses
        'a.apiSubSet',  # Subset of the API Listing [string api1, string api2, ... , string apiN]
        'a.version',    # Telemachus Version
        ]
