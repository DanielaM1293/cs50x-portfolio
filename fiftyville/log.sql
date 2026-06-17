-- Keep a log of any SQL queries you execute as you solve the mystery.
-- Buscar el reporte del crimen
SELECT *
FROM crime_scene_reports
WHERE year = 2025
AND month = 7
AND day = 28
AND street = 'Humphrey Street';

-- Revisar entrevistas de los testigos
SELECT *
FROM interviews
WHERE year = 2025
AND month = 7
AND day = 28;

-- Revisar vehículos que salieron de la panadería
SELECT *
FROM bakery_security_logs
WHERE year = 2025
AND month = 7
AND day = 28
AND hour = 10
AND minute BETWEEN 15 AND 25;

-- Revisar retiros en el ATM de Leggett Street
SELECT *
FROM atm_transactions
WHERE year = 2025
AND month = 7
AND day = 28
AND atm_location = 'Leggett Street'
AND transaction_type = 'withdraw';

-- Revisar llamadas de menos de un minuto
SELECT *
FROM phone_calls
WHERE year = 2025
AND month = 7
AND day = 28
AND duration < 60;

-- Revisar los vuelos del día siguiente
SELECT *
FROM flights
WHERE year = 2025
AND month = 7
AND day = 29
ORDER BY hour, minute;
