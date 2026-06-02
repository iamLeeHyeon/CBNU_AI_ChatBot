import React, { useState, useEffect } from 'react';

const LMS_BASE = "https://lms.chungbuk.ac.kr";

const formatDueDate = (timestamp) => {
  if (!timestamp) return "기한 없음";
  return new Date(timestamp * 1000).toLocaleString("ko-KR", {
    year: "numeric", month: "2-digit", day: "2-digit",
    hour: "2-digit", minute: "2-digit",
  });
};

const LMSDashboard = ({ onLogout }) => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [syncing, setSyncing] = useState(false);

  const fetchDashboardData = async () => {
    try {
      const response = await fetch('/api/lms/dashboard', {
        credentials: 'include'
      });

      if (response.status === 401) {
        onLogout();
        return;
      }

      const result = await response.json();
      if (result.success) {
        setData(result);
      } else {
        setError('데이터를 불러오지 못했습니다.');
      }
    } catch (err) {
      setError('서버와 연결할 수 없습니다.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const handleForceSync = async () => {
    setSyncing(true);
    try {
      const res = await fetch('/api/lms/sync', { method: 'POST', credentials: 'include' });
      if (res.status === 401) {
        onLogout();
        return;
      }
      if (res.ok) {
        await fetchDashboardData();
      } else {
        setError('동기화에 실패했습니다.');
      }
    } catch {
      setError('서버와 연결할 수 없습니다.');
    } finally {
      setSyncing(false);
    }
  };

  if (loading) return <div>LMS 정보를 불러오는 중입니다...</div>;
  if (error) return <div style={{ color: 'red' }}>{error}</div>;

  return (
    <div className="lms-dashboard">
      <header style={{ display: 'flex', justifyContent: 'space-between', padding: '10px 0' }}>
        <h2>반갑습니다, {data?.user_name}님!</h2>
        <div>
          <button onClick={handleForceSync}>🔄 정보 동기화</button>
          <button onClick={onLogout} style={{ marginLeft: '10px' }}>로그아웃</button>
        </div>
      </header>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' }}>

        {/* 강좌 */}
        <section style={cardStyle}>
          <h3>📚 내 강좌</h3>
          <ul>
            {data?.courses?.map((course) => (
              <li key={course.id}>
                <a
                  href={`${LMS_BASE}/course/view.php?id=${course.id}`}
                  target="_blank"
                  rel="noreferrer"
                >
                  {course.full_name}
                </a>
              </li>
            ))}
          </ul>
        </section>

        {/* 과제 */}
        <section style={cardStyle}>
          <h3>📝 마감 임박 과제</h3>
          <ul>
            {data?.assignments
              ?.filter(a => !a.submitted)
              .slice(0, 5)
              .map((assign) => (
                <li key={assign.id}>
                  <strong>{assign.course_name}</strong>: {assign.name}<br />
                  <span style={{ color: 'red' }}>마감: {formatDueDate(assign.due_date)}</span>
                  {assign.cmid && (
                    <>
                      {' '}
                      <a
                        href={`${LMS_BASE}/mod/assign/view.php?id=${assign.cmid}`}
                        target="_blank"
                        rel="noreferrer"
                        style={{ fontSize: '0.85em', color: '#1a73e8' }}
                      >
                        → 제출하기
                      </a>
                    </>
                  )}
                </li>
              ))}
          </ul>
        </section>

        {/* 일정 */}
        <section style={cardStyle}>
          <h3>📅 일정 (과제 마감)</h3>
          <ul style={{ listStyleType: 'none', padding: 0 }}>
            {data?.assignments?.map((assign) => {
              if (!assign.due_date) return null;
              return (
                <li key={assign.id} style={{ marginBottom: '5px', padding: '5px', background: '#f0f0f0', borderRadius: '4px' }}>
                  <span style={{ fontWeight: 'bold' }}>
                    {new Date(assign.due_date * 1000).toLocaleDateString("ko-KR")}
                  </span>{' '}
                  - <span style={{ color: '#555', fontSize: '0.85em' }}>[{assign.course_name}]</span> {assign.name}
                  {assign.cmid && (
                    <>
                      {' '}
                      <a
                        href={`${LMS_BASE}/mod/assign/view.php?id=${assign.cmid}`}
                        target="_blank"
                        rel="noreferrer"
                        style={{ fontSize: '0.8em', color: '#1a73e8' }}
                      >
                        → 제출하기
                      </a>
                    </>
                  )}
                </li>
              );
            })}
          </ul>
        </section>

        {/* 성적 */}
        <section style={cardStyle}>
          <h3>🎓 이번 학기 성적</h3>
          {data?.grades?.length > 0 ? (
            <ul>
              {data.grades.map((g, idx) => (
                <li key={idx}>
                  <strong>{g.course_name}</strong>: {g.grade ?? '미공개'}
                </li>
              ))}
            </ul>
          ) : (
            <div style={{ padding: '20px', textAlign: 'center', color: '#666' }}>
              <p>성적 정보가 없습니다.</p>
            </div>
          )}
        </section>

      </div>
    </div>
  );
};

const cardStyle = {
  border: '1px solid #ccc',
  borderRadius: '8px',
  padding: '15px',
  backgroundColor: '#fff',
  boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
};

export default LMSDashboard;
