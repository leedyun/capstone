import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../auth/store';
import api from '../api/axiosConfig';

export default function KakaoCallback() {
    const navigate = useNavigate();
    const { setAuth } = useAuth();

    useEffect(() => {
        const processKakaoLogin = async () => {
            try {
                const code = new URLSearchParams(window.location.search).get('code');
                console.log('Received code:', code);

                if (!code) {
                    console.error('No code received');
                    navigate('/login');
                    return;
                }

                const response = await api.get('api/oauth/login', {
                    params: {
                        code,
                        redirect_uri: 'http://localhost:5173/api/oauth/login'
                    }
                });

                console.log('Login response:', response.data);

                const { access_token, user } = response.data;
                setAuth({
                    access: access_token,
                    user: user
                });

                navigate('/profile');
            } catch (error) {
                console.error('카카오 로그인 처리 중 오류:', error);
                navigate('/login');
            }
        };

        processKakaoLogin();
    }, [navigate, setAuth]);

    return (
        <div className="h-screen flex items-center justify-center">
            <p>카카오 로그인 처리 중...</p>
        </div>
    );
} 