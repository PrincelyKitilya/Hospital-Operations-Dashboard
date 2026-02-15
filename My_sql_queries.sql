--total revenue
SELECT 
	SUM(amount) as revenue
FROM Bills
WHERE paymentStatus = 'Paid';


--patient count 
SELECT 
	COUNT(*) as patient_count
FROM Patients;


--appointment_stats_query
SELECT
	COUNT(*) as total,
	100.0 * SUM(CASE WHEN status = 'Completed' THEN 1 ELSE 0 END)/ COUNT(*) AS completion_rate
FROM Appointments;

--patients who did not come to their appointment
SELECT 
	100.0 * SUM(CASE WHEN status = 'No-show' THEN 1 ELSE 0 END)/ COUNT(*) as rate
FROM Appointments;

--monthly revenue 
SELECT
    TO_CHAR(billDate, 'YYYY-MM') AS Month,
    SUM(amount) AS Revenue,
    paymentStatus
FROM Bills
GROUP BY TO_CHAR(billDate, 'YYYY-MM'), paymentStatus
ORDER BY Month;

--Treatment Type Revenue
SELECT 
	t.treatmentType,
	SUM(b.amount) as revenue
FROM treatments AS t
INNER JOIN Bills as b
ON t.treatmentID = b.treatmentID
WHERE b.paymentStatus = 'Paid'
GROUP BY t.treatmentType
ORDER BY revenue DESC;



--Payment Status Distribution
SELECT 
	paymentStatus,
	COUNT(*) AS pCount,
	SUM(amount) AS TotalAmount
FROM Bills
GROUP BY paymentStatus;


--Patient Demographics
SELECT 
    insuranceProvider,
    COUNT(*) AS PatientCount,
    AVG(EXTRACT(YEAR FROM AGE(CURRENT_DATE, dateOfBirth))) AS AvgAge,
    COUNT(DISTINCT a.appointmentID) AS TotalAppointments
FROM Patients p
LEFT JOIN Appointments a ON p.patientID = a.patientID
GROUP BY insuranceProvider;

--
