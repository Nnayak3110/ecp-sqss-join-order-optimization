-- Query - 01
SELECT * FROM 
circuits,
 constructorresults,
 constructors,
 constructorstandings,
 races
WHERE 
constructorresults.constructorId=constructors.constructorId
AND constructorresults.raceId=races.raceId
AND constructorstandings.constructorId=constructors.constructorId
AND constructorstandings.raceId=races.raceId
AND races.circuitId=circuits.circuitId;

-- Query - 02
SELECT * FROM 
circuits,
 constructorresults,
 constructors,
 qualifying,
 races
WHERE 
constructorresults.constructorId=constructors.constructorId
AND constructorresults.raceId=races.raceId
AND qualifying.constructorId=constructors.constructorId
AND qualifying.raceId=races.raceId
AND races.circuitId=circuits.circuitId;

-- Query - 03
SELECT * FROM 
circuits,
 constructorresults,
 constructors,
 races,
 seasons
WHERE 
constructorresults.constructorId=constructors.constructorId
AND constructorresults.raceId=races.raceId
AND races.circuitId=circuits.circuitId
AND races.year=seasons.year;

-- Query - 04
SELECT * FROM 
circuits,
 constructorresults,
 constructorstandings,
 driverstandings,
 races
WHERE 
constructorresults.raceId=races.raceId
AND constructorstandings.raceId=races.raceId
AND driverstandings.raceId=races.raceId
AND races.circuitId=circuits.circuitId;

-- Query - 05
SELECT * FROM 
circuits,
 constructorresults,
 constructorstandings,
 laptimes,
 races
WHERE 
constructorresults.raceId=races.raceId
AND constructorstandings.raceId=races.raceId
AND laptimes.raceId=races.raceId
AND races.circuitId=circuits.circuitId;

-- Query - 06
SELECT * FROM 
circuits,
 constructorstandings,
 drivers,
 laptimes,
 races
WHERE 
constructorstandings.raceId=races.raceId
AND laptimes.driverId=drivers.driverId
AND laptimes.raceId=races.raceId
AND races.circuitId=circuits.circuitId;

-- Query - 07
SELECT * FROM 
constructorresults,
 constructorstandings,
 driverstandings,
 laptimes,
 races
WHERE 
constructorresults.raceId=races.raceId
AND constructorstandings.raceId=races.raceId
AND driverstandings.raceId=races.raceId
AND laptimes.raceId=races.raceId;

-- Query - 08
SELECT * FROM 
constructorresults,
 laptimes,
 pitstops,
 qualifying,
 races
WHERE 
constructorresults.raceId=races.raceId
AND laptimes.raceId=races.raceId
AND pitstops.raceId=races.raceId
AND qualifying.raceId=races.raceId;

-- Query - 09
SELECT * FROM 
constructors,
 driverstandings,
 pitstops,
 qualifying,
 races
WHERE 
driverstandings.raceId=races.raceId
AND pitstops.raceId=races.raceId
AND qualifying.constructorId=constructors.constructorId
AND qualifying.raceId=races.raceId;

-- Query - 10
SELECT * FROM 
circuits,
 constructorresults,
 constructors,
 races,
 results
WHERE 
constructorresults.constructorId=constructors.constructorId
AND constructorresults.raceId=races.raceId
AND races.circuitId=circuits.circuitId
AND results.constructorId=constructors.constructorId
AND results.raceId=races.raceId;