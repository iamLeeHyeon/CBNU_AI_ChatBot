import React, { useState, useEffect } from 'react';

const LMSDashboard = ({ onLogout }) => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [syncing, setSyncing] = useState(false); // 리로드 버튼 전용 로딩
  const [error, setError] = useState('');

  // 1. 페이지 로드 및 새로고침 시: 백엔드에서 '저장된 데이터'만 빠르게 가져오기
  const fetchDashboardData = async () => {
    try {
      const response = await fetch('/api/lms/dashboard', {
        credentials: 'include' // 쿠키(세션)를 백엔드에 전달
      });
      
      if (response.status === 401) {
        // 세션이 없거나 만료됨 -> 로그인 화면으로 쫓아내기
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

  // 2. 수동 리로드 버튼: 사용자가 원할 때만 다시 크롤링
  // (주의: 크롤러가 다시 돌려면 학번/비번이 필요한데, 보안상 세션에 비번을 저장하지 않으므로
  // 가장 좋은 방법은 동기화 버튼 클릭 시 비밀번호만 모달창으로 한 번 물어보거나, 
  // 로그아웃 후 다시 로그인하게 유도하는 것입니다. 여기서는 알림창으로 대체합니다.)
  const handleForceSync = () => {
    alert("정보를 다시 동기화하려면 보안을 위해 재로그인이 필요합니다.");
    onLogout(); 
    // 나중에 백엔드를 수정하여 자동 재크롤링이 가능해지면 이 부분에 POST 요청을 연결하면 됩니다.
  };

  if (loading) return <div>LMS 정보를 불러오는 중입니다...</div>;
  if (error) return <div style={{color: 'red'}}>{error}</div>;

  return (
    <div className="lms-dashboard">
      <header style={{ display: 'flex', justifyContent: 'space-between', padding: '10px 0' }}>
        <h2>반갑습니다, {data?.user_name}님!</h2>
        <div>
          <button onClick={handleForceSync} disabled={syncing}>
            {syncing ? '동기화 중...' : '🔄 정보 동기화'}
          </button>
          <button onClick={onLogout} style={{ marginLeft: '10px' }}>로그아웃</button>
        </div>
      </header>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' }}>
        
        {/* 1. 강좌 영역 */}
        <section style={cardStyle}>
          <h3>📚 내 강좌</h3>
          <ul>
            {data?.courses?.map((course, idx) => (
              <li key={idx}>
                <a href={course.url} target="_blank" rel="noreferrer">{course.name}</a>
              </li>
            ))}
          </ul>
        </section>

        {/* 2. 과제 영역 */}
        <section style={cardStyle}>
          <h3>📝 마감 임박 과제</h3>
          <ul>
            {data?.assignments?.filter(a => !a.submitted).slice(0, 5).map((assign, idx) => (
              <li key={idx}>
                <strong>{assign.course_name}</strong>: {assign.title} <br/>
                <span style={{ color: 'red' }}>마감: {assign.due_date}</span>
              </li>
            ))}
          </ul>
        </section>

        {/* 3. 캘린더 영역 (과제 마감일 기반으로 임시 구현) */}
        <section style={cardStyle}>
          <h3>📅 일정 (과제 마감)</h3>
          <ul style={{ listStyleType: 'none', padding: 0 }}>
            {data?.assignments?.map((assign, idx) => {
              if (!assign.due_date || assign.due_date === "~") return null;
              return (
                <li key={idx} style={{ marginBottom: '5px', padding: '5px', background: '#f0f0f0', borderRadius: '4px' }}>
                  <span style={{ fontWeight: 'bold' }}>{assign.due_date.split(' ')[0]}</span> - {assign.title}
                </li>
              );
            })}
          </ul>
        </section>

        {/* 4. 성적 영역 (백엔드 추가 전까지 Placeholder) */}
        <section style={cardStyle}>
          <h3>A+ 이번 학기 성적</h3>
          <div style={{ padding: '20px', textAlign: 'center', color: '#666' }}>
            <p>🚧 성적 연동 기능은 현재 개발 중입니다.</p>
          </div>
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
  boxShadow: '0 2px 4px rgba(0,0,0,0.1)'
};

export default LMSDashboard;