export default function Dashboard() {
  const { data: students, isLoading } = useStudents();
  const totalStudents = students?.length || 0;
  const averageScore = totalStudents > 0 
    ? (students!.reduce((acc, curr) => acc + curr.average, 0) / totalStudents).toFixed(1)
    : "0.0";

  return (
    <div className="min-h-screen bg-[#F8FAFC]">
      <header className="bg-white border-b p-4 flex justify-between items-center">
        <h1 className="text-2xl font-bold">EduMetrics</h1>
        <AddStudentDialog />
      </header>
      <main className="p-8">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          <StatsCard label="Total Students" value={totalStudents} />
          <StatsCard label="Cohort Average" value={averageScore} />
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {students?.map(student => <StudentCard key={student.id} student={student} />)}
        </div>
      </main>
    </div>
  );
}
