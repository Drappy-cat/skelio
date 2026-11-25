import { createContext, FormEvent, ReactNode, useContext, useEffect, useRef, useState } from 'react'
import pushupHero from './assets/pushup-hero.png'
import skelioLogo from './assets/skelio-logo.webp'

type Screen =
  | 'welcome'
  | 'login'
  | 'register'
  | 'forgotPassword'
  | 'home'
  | 'analyze'
  | 'history'
  | 'analytics'
  | 'sessionDetail'
  | 'profile'
  | 'notifications'
  | 'editProfile'
  | 'settings'
  | 'help'
  | 'about'

type Language = 'id' | 'en'

const english: Record<string, string> = {
  'UNESA · 2026': 'UNESA · 2026',
  'AI-POWERED MOVEMENT COACH': 'AI-POWERED MOVEMENT COACH',
  'Setiap repetisi,': 'Every repetition,',
  'lebih presisi.': 'more precise.',
  'Analisis Push-up, Sit-up, dan Squat secara real-time, langsung dari kamera ponselmu.': 'Analyze Push-ups, Sit-ups, and Squats in real time, directly from your phone camera.',
  'Mulai latihan': 'Start training',
  'Sudah punya akun?': 'Already have an account?',
  'Masuk di sini': 'Sign in here',
  'SELAMAT DATANG KEMBALI': 'WELCOME BACK',
  'BERGABUNG DENGAN SKELIO': 'JOIN SKELIO',
  'Masuk ke akunmu': 'Sign in to your account',
  'Buat akun baru': 'Create a new account',
  'Lanjutkan latihan dan pantau progres gerakanmu.': 'Continue training and track your movement progress.',
  'Mulai perjalanan latihan yang lebih presisi.': 'Start a more precise training journey.',
  'Nama lengkap': 'Full name',
  'Masukkan nama lengkap': 'Enter your full name',
  'Kata sandi': 'Password',
  'Minimal 8 karakter': 'At least 8 characters',
  'Ingat saya': 'Remember me',
  'Lupa kata sandi?': 'Forgot password?',
  'Saya menyetujui': 'I agree to the',
  'Syarat Penggunaan': 'Terms of Use',
  'dan': 'and',
  'Kebijakan Privasi': 'Privacy Policy',
  'Masuk': 'Sign in',
  'Buat Akun': 'Create account',
  'Belum punya akun?': "Don't have an account?",
  'Daftar': 'Register',
  'Selamat pagi,': 'Good morning,',
  'WEEKLY STREAK': 'WEEKLY STREAK',
  'Terus bergerak!': 'Keep moving!',
  'Kamu sudah aktif 4 hari berturut-turut.': 'You have been active for 4 days in a row.',
  'HARI': 'DAYS',
  'SIAP BERLATIH?': 'READY TO TRAIN?',
  'Mulai analisis': 'Start analysis',
  'Lihat semua': 'View all',
  'Push-up Analysis': 'Push-up Analysis',
  'Deteksi sudut siku & repetisi secara real-time': 'Detect elbow angle and repetitions in real time',
  'Lower body': 'Lower body',
  'Upper body': 'Upper body',
  '7 HARI TERAKHIR': 'LAST 7 DAYS',
  'Ringkasan aktivitas': 'Activity summary',
  'Menit latihan': 'Training minutes',
  'Akurasi rata-rata': 'Average accuracy',
  'Beranda': 'Home',
  'Analisis': 'Analysis',
  'Riwayat': 'History',
  'Profil': 'Profile',
  'LIVE ANALYSIS': 'LIVE ANALYSIS',
  'Posisikan seluruh tubuh': 'Position your entire body',
  'Pastikan area latihan cukup terang': 'Make sure the training area is well lit',
  'JENIS LATIHAN': 'EXERCISE TYPE',
  'REPETISI': 'REPETITIONS',
  'KEDALAMAN': 'DEPTH',
  'POSTUR': 'POSTURE',
  'Baik': 'Good',
  'Selesai Analisis': 'Finish Analysis',
  'Mulai Analisis': 'Start Analysis',
  'PROGRES LATIHAN': 'TRAINING PROGRESS',
  'FEBRUARI 2026': 'FEBRUARY 2026',
  '8 sesi': '8 sessions',
  '+24% dari Januari': '+24% from January',
  'Aktivitas terbaru': 'Recent activity',
  'Filter': 'Filter',
  'Semua': 'All',
  'Hari ini, 08:24': 'Today, 08:24',
  'Kemarin, 17:10': 'Yesterday, 17:10',
  'AKUN SAYA': 'MY ACCOUNT',
  'MEMBER SEJAK 2026': 'MEMBER SINCE 2026',
  'Total sesi': 'Total sessions',
  'Total reps': 'Total reps',
  'Avg. skor': 'Avg. score',
  'Edit profil': 'Edit profile',
  'Pengaturan aplikasi': 'App settings',
  'Bantuan & tentang SKELIO': 'Help & about SKELIO',
  'Bantuan SKELIO': 'SKELIO Help',
  'Tentang kami': 'About us',
  'TIM PENGEMBANG': 'DEVELOPMENT TEAM',
  'Dibangun bersama untuk gerakan yang lebih baik.': 'Built together for better movement.',
  'SKELIO dikembangkan oleh Kelompok 11 Big Data, Program Studi S1 Teknik Informatika Universitas Negeri Surabaya.': 'SKELIO was developed by Group 11 Big Data, Undergraduate Informatics Program at Universitas Negeri Surabaya.',
  'ANGGOTA TIM': 'TEAM MEMBERS',
  'Mahasiswa S1 Teknik Informatika': 'Undergraduate Informatics Student',
  'KELOMPOK 11 · BIG DATA UNESA 2026': 'GROUP 11 · BIG DATA UNESA 2026',
  'Tim di balik SKELIO': 'The team behind SKELIO',
  'SKELIO merupakan proyek Kelompok 11 untuk mata kuliah Big Data, Program Studi S1 Teknik Informatika, Universitas Negeri Surabaya.': 'SKELIO is a Group 11 project for the Big Data course, Undergraduate Informatics Program, Universitas Negeri Surabaya.',
  'Kelompok 11 · Big Data': 'Group 11 · Big Data',
  'Dosen pembimbing': 'Academic advisor',
  'Keluar': 'Sign out',
  'PREFERENSI APLIKASI': 'APP PREFERENCES',
  'Pengaturan': 'Settings',
  'ANALISIS': 'ANALYSIS',
  'Suara feedback': 'Voice feedback',
  'Instruksi suara selama latihan': 'Voice instructions during training',
  'Getaran': 'Vibration',
  'Getaran saat repetisi tervalidasi': 'Vibrate when a repetition is validated',
  'Simpan video': 'Save video',
  'Simpan rekaman analisis otomatis': 'Automatically save analysis recordings',
  'NOTIFIKASI': 'NOTIFICATIONS',
  'Pengingat latihan': 'Training reminders',
  'Pengingat target mingguan': 'Weekly target reminders',
  'Tips postur': 'Posture tips',
  'Rekomendasi berdasarkan hasil latihan': 'Recommendations based on training results',
  'Bahasa': 'Language',
  'Bahasa Indonesia': 'Indonesian',
  'English': 'English',
  'PEMBARUAN': 'UPDATES',
  'Notifikasi': 'Notifications',
  'Hasil analisis': 'Analysis result',
  'POSTUR KESELURUHAN': 'OVERALL POSTURE',
  'Sangat baik': 'Excellent',
  'Gerakan stabil dan kedalaman repetisi konsisten.': 'Stable movement with consistent repetition depth.',
  'DURASI': 'DURATION',
  'AKURASI': 'ACCURACY',
  'SUDUT SIKU': 'ELBOW ANGLE',
  'Waktu aktif': 'Active time',
  'Rentang optimal': 'Optimal range',
  'FEEDBACK AI': 'AI FEEDBACK',
  'Pertahankan posisi tubuhmu': 'Maintain your body position',
  'Ulangi latihan': 'Repeat workout',
  'INFORMASI PRIBADI': 'PERSONAL INFORMATION',
  'Program studi': 'Study program',
  'Simpan perubahan': 'Save changes',
  'Perubahan profil berhasil disimpan.': 'Profile changes saved successfully.',
  'PUSAT INFORMASI': 'INFORMATION CENTER',
  'Bantuan': 'Help',
  'Pertanyaan umum': 'Frequently asked questions',
  'Hubungi tim SKELIO': 'Contact the SKELIO team',
  'Kelompok 11 Big Data UNESA': 'Group 11 Big Data UNESA',
  'BANTUAN AKUN': 'ACCOUNT HELP',
  'Atur ulang sandi': 'Reset password',
  'Kirim tautan pemulihan': 'Send recovery link',
  'Kembali ke login': 'Back to login',
  'Periksa emailmu': 'Check your email',
  'Tautan untuk mengatur ulang kata sandi telah dikirim ke email yang kamu masukkan.': 'A password reset link has been sent to the email address you entered.',
  'Masukkan email akun SKELIO. Kami akan mengirimkan tautan pemulihan kata sandi.': 'Enter your SKELIO account email. We will send you a password recovery link.',
  'Ubah foto': 'Change photo',
  'Clean reps tercatat': 'Clean reps recorded',
  'Durasi tertahan': 'Hold duration',
  '+3% dari sesi lalu': '+3% from last session',
  'Edit profil': 'Edit profile',
  'Baru saja': 'Just now',
  '2 jam lalu': '2 hours ago',
  'Kemarin': 'Yesterday',
  'Analisis selesai': 'Analysis complete',
  'Skor Push-up kamu hari ini mencapai 94. Lihat detail hasil latihan.': 'Your Push-up score reached 94 today. View your workout details.',
  'Target mingguan': 'Weekly target',
  'Satu sesi lagi untuk menyelesaikan target latihan minggu ini.': 'One more session to complete this week’s training target.',
  'Jaga posisi pinggul tetap sejajar saat melakukan Push-up.': 'Keep your hips aligned while performing Push-ups.',
  'AKSES KAMERA': 'CAMERA ACCESS',
  'Kamera digunakan hanya untuk menganalisis gerakanmu.': 'The camera is only used to analyze your movement.',
  'Video tidak disimpan kecuali kamu mengaktifkan penyimpanan melalui Pengaturan.': 'Video is not saved unless you enable recording in Settings.',
  'Izinkan kamera': 'Allow camera',
  'Nanti saja': 'Not now',
  'Menyiapkan kamera...': 'Preparing camera...',
  'Kamera siap': 'Camera ready',
  'Seluruh tubuh harus terlihat di dalam bingkai.': 'Your entire body must be visible inside the frame.',
  'Izin kamera ditolak': 'Camera permission denied',
  'Aktifkan izin kamera melalui pengaturan perangkat untuk memulai analisis.': 'Enable camera access in your device settings to start the analysis.',
  'Coba lagi': 'Try again',
  'Postur baik': 'Good posture',
  'Gerakan stabil dan siap dihitung.': 'Movement is stable and ready to be counted.',
  'Belum ada aktivitas': 'No activity yet',
  'Mulai latihan pertamamu untuk melihat hasil analisis di sini.': 'Start your first workout to see analysis results here.',
  'DETAIL AKTIVITAS': 'ACTIVITY DETAILS',
  'Statistik latihan': 'Training statistics',
  'Total latihan': 'Total workouts',
  'Total waktu': 'Total time',
  'Rata-rata skor': 'Average score',
  'Repetisi bersih': 'Clean repetitions',
  'Aktivitas latihan': 'Training activity',
  'Minggu': 'Week',
  'Bulan': 'Month',
  '3 Bulan': '3 Months',
  'sesi': 'sessions',
  'menit': 'minutes',
  'Lihat statistik lengkap': 'View complete statistics',
  'SKOR': 'SCORE',
  'Postur bahu dan pinggul sudah sejajar. Pada dua repetisi terakhir, usahakan siku tidak terlalu melebar untuk menjaga beban tetap stabil.': 'Your shoulders and hips are well aligned. For the final two repetitions, keep your elbows from flaring too wide to maintain a stable load.',
  'Bagaimana memulai analisis?': 'How do I start an analysis?',
  'Pilih menu Analisis, tentukan Push-up, Sit-up, atau Squat, lalu posisikan seluruh tubuh di dalam bingkai kamera.': 'Open Analysis, choose Push-up, Sit-up, or Squat, then position your entire body inside the camera frame.',
  'Mengapa repetisi tidak terhitung?': 'Why are my repetitions not counted?',
  'Pastikan pencahayaan cukup dan gerakan mencapai ambang kedalaman yang ditentukan.': 'Make sure the lighting is sufficient and your movement reaches the required depth threshold.',
  'Apakah video saya disimpan?': 'Is my video saved?',
  'Video tidak disimpan secara otomatis kecuali opsi Simpan video diaktifkan pada Pengaturan.': 'Videos are not saved automatically unless Save video is enabled in Settings.',
}

const LanguageContext = createContext<{
  language: Language
  setLanguage: (language: Language) => void
}>({ language: 'id', setLanguage: () => undefined })

function useLanguage() {
  const context = useContext(LanguageContext)
  return {
    ...context,
    t: (text: string) => context.language === 'en' ? english[text] || text : text,
  }
}

function Icon({
  name,
  size = 22,
  filled = false,
}: {
  name: string
  size?: number
  filled?: boolean
}) {
  const paths: Record<string, ReactNode> = {
    home: (
      <>
        <path d="m3 11 9-8 9 8" />
        <path d="M5 10v10h14V10M9 20v-6h6v6" />
      </>
    ),
    scan: (
      <>
        <path d="M8 3H4a1 1 0 0 0-1 1v4M16 3h4a1 1 0 0 1 1 1v4M8 21H4a1 1 0 0 1-1-1v-4M16 21h4a1 1 0 0 0 1-1v-4" />
        <circle cx="12" cy="8" r="2" />
        <path d="M8 18v-3a4 4 0 0 1 8 0v3M12 10v4" />
      </>
    ),
    history: (
      <>
        <path d="M3 12a9 9 0 1 0 3-6.7L3 8" />
        <path d="M3 3v5h5M12 7v5l3 2" />
      </>
    ),
    user: (
      <>
        <circle cx="12" cy="8" r="4" />
        <path d="M4 21a8 8 0 0 1 16 0" />
      </>
    ),
    users: (
      <>
        <circle cx="9" cy="8" r="3" />
        <path d="M3 20a6 6 0 0 1 12 0M16 5a3 3 0 0 1 0 6M17 14a5 5 0 0 1 4 5" />
      </>
    ),
    bell: (
      <>
        <path d="M18 8a6 6 0 0 0-12 0c0 7-3 7-3 9h18c0-2-3-2-3-9M10 21h4" />
      </>
    ),
    arrow: <path d="m9 18 6-6-6-6" />,
    back: <path d="m15 18-6-6 6-6" />,
    play: <path d="m8 5 11 7-11 7V5Z" />,
    flame: (
      <path d="M13 22c4-1 7-4 7-9 0-3-2-6-5-9 0 3-2 5-4 6 0-2-1-4-3-5 0 4-4 6-4 11 0 3 2 5 5 6-1-1-2-3-1-5 1 1 2 2 3 2 2-1 3-3 3-5 2 3 2 6-1 8Z" />
    ),
    clock: (
      <>
        <circle cx="12" cy="12" r="9" />
        <path d="M12 7v5l3 2" />
      </>
    ),
    target: (
      <>
        <circle cx="12" cy="12" r="9" />
        <circle cx="12" cy="12" r="4" />
      </>
    ),
    squat: (
      <>
        <circle cx="15" cy="4" r="2" />
        <path d="m14 7-3 5 4 3 3 6M11 12l-5 1-3 4M15 15l-5 6" />
      </>
    ),
    pushup: (
      <>
        <circle cx="18" cy="9" r="2" />
        <path d="m16 11-6 3-6-1M10 14l4 4M4 13l-2 6M14 18h7" />
      </>
    ),
    situp: (
      <>
        <circle cx="8" cy="6" r="2" />
        <path d="m9 8 4 5 5 2M13 13l-4 5M18 15l4 4M9 18H3" />
      </>
    ),
    chevronDown: <path d="m6 9 6 6 6-6" />,
    camera: (
      <>
        <rect x="3" y="6" width="18" height="14" rx="2" />
        <circle cx="12" cy="13" r="4" />
        <path d="m8 6 1-2h6l1 2" />
      </>
    ),
    settings: (
      <>
        <circle cx="12" cy="12" r="3" />
        <path d="M19.4 15a1.7 1.7 0 0 0 .3 1.9l.1.1-2.8 2.8-.1-.1a1.7 1.7 0 0 0-1.9-.3 1.7 1.7 0 0 0-1 1.6v.2h-4V21a1.7 1.7 0 0 0-1-1.6 1.7 1.7 0 0 0-1.9.3l-.1.1L4.2 17l.1-.1a1.7 1.7 0 0 0 .3-1.9A1.7 1.7 0 0 0 3 14H2.8v-4H3a1.7 1.7 0 0 0 1.6-1 1.7 1.7 0 0 0-.3-1.9L4.2 7 7 4.2l.1.1a1.7 1.7 0 0 0 1.9.3A1.7 1.7 0 0 0 10 3V2.8h4V3a1.7 1.7 0 0 0 1 1.6 1.7 1.7 0 0 0 1.9-.3l.1-.1L19.8 7l-.1.1a1.7 1.7 0 0 0-.3 1.9 1.7 1.7 0 0 0 1.6 1h.2v4H21a1.7 1.7 0 0 0-1.6 1Z" />
      </>
    ),
    help: (
      <>
        <circle cx="12" cy="12" r="9" />
        <path d="M9.8 9a2.4 2.4 0 1 1 3.5 2.1c-.8.5-1.3.9-1.3 1.9M12 17h.01" />
      </>
    ),
    logout: (
      <>
        <path d="M10 17l5-5-5-5M15 12H3M14 4h5a2 2 0 0 1 2 2v12a2 2 0 0 1-2 2h-5" />
      </>
    ),
    eye: (
      <>
        <path d="M2 12s3.5-6 10-6 10 6 10 6-3.5 6-10 6S2 12 2 12Z" />
        <circle cx="12" cy="12" r="2.5" />
      </>
    ),
    mail: (
      <>
        <rect x="3" y="5" width="18" height="14" rx="2" />
        <path d="m3 7 9 6 9-6" />
      </>
    ),
    lock: (
      <>
        <rect x="4" y="10" width="16" height="11" rx="2" />
        <path d="M8 10V7a4 4 0 0 1 8 0v3" />
      </>
    ),
  }
  return (
    <svg
      aria-hidden="true"
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill={filled ? 'currentColor' : 'none'}
      stroke="currentColor"
      strokeWidth="1.8"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      {paths[name]}
    </svg>
  )
}

function Logo({ light = false }: { light?: boolean }) {
  return (
    <div className={`mobile-logo ${light ? 'light' : ''}`}>
      <img src={skelioLogo} alt="Logo SKELIO" />
    </div>
  )
}

function StatusBar({ light = false }: { light?: boolean }) {
  return (
    <div className={`status-bar ${light ? 'light' : ''}`}>
      <b>9:41</b>
      <div>
        <span className="signal">▮▮▮</span>
        <span className="wifi">⌁</span>
        <span className="battery"><i /></span>
      </div>
    </div>
  )
}

function Welcome({ go }: { go: (screen: Screen) => void }) {
  const { t } = useLanguage()
  return (
    <div className="welcome-screen">
      <StatusBar light />
      <div className="welcome-media">
        <img src={pushupHero} alt="Atlet melakukan push-up dengan postur yang terdeteksi" />
        <div className="welcome-shade" />
        <div className="welcome-top">
          <Logo light />
          <span>{t('UNESA · 2026')}</span>
        </div>
      </div>
      <div className="welcome-panel">
        <span className="kicker">{t('AI-POWERED MOVEMENT COACH')}</span>
        <h1>
          {t('Setiap repetisi,')}
          <br />
          <em>{t('lebih presisi.')}</em>
        </h1>
        <p>{t('Analisis Push-up, Sit-up, dan Squat secara real-time, langsung dari kamera ponselmu.')}</p>
        <button className="main-button" onClick={() => go('register')}>
          {t('Mulai latihan')} <Icon name="arrow" size={18} />
        </button>
        <button className="text-button" onClick={() => go('login')}>
          {t('Sudah punya akun?')} <b>{t('Masuk di sini')}</b>
        </button>
      </div>
    </div>
  )
}

function AuthScreen({
  mode,
  go,
}: {
  mode: 'login' | 'register'
  go: (screen: Screen) => void
}) {
  const { t } = useLanguage()
  const [showPassword, setShowPassword] = useState(false)
  const isLogin = mode === 'login'
  const submit = (event: FormEvent) => {
    event.preventDefault()
    go('home')
  }
  return (
    <div className="plain-screen auth-mobile">
      <StatusBar />
      <button className="round-back" onClick={() => go('welcome')} aria-label="Kembali">
        <Icon name="back" size={20} />
      </button>
      <div className="auth-heading">
        <Logo />
        <div className="auth-pushup-visual">
          <img src={pushupHero} alt="Deteksi gerakan push-up" />
        </div>
        <span className="kicker">{t(isLogin ? 'SELAMAT DATANG KEMBALI' : 'BERGABUNG DENGAN SKELIO')}</span>
        <h1>{t(isLogin ? 'Masuk ke akunmu' : 'Buat akun baru')}</h1>
        <p>
          {t(isLogin
            ? 'Lanjutkan latihan dan pantau progres gerakanmu.'
            : 'Mulai perjalanan latihan yang lebih presisi.')}
        </p>
      </div>
      <form className="mobile-form" onSubmit={submit}>
        {!isLogin && (
          <label>
            <span>{t('Nama lengkap')}</span>
            <div className="input-wrap">
              <Icon name="user" size={19} />
              <input required type="text" placeholder={t('Masukkan nama lengkap')} />
            </div>
          </label>
        )}
        <label>
          <span>Email</span>
          <div className="input-wrap">
            <Icon name="mail" size={19} />
            <input required type="email" placeholder="nama@email.com" />
          </div>
        </label>
        <label>
          <span>{t('Kata sandi')}</span>
          <div className="input-wrap">
            <Icon name="lock" size={19} />
            <input
              required
              minLength={8}
              type={showPassword ? 'text' : 'password'}
              placeholder={t('Minimal 8 karakter')}
            />
            <button type="button" onClick={() => setShowPassword(!showPassword)}>
              <Icon name="eye" size={19} />
            </button>
          </div>
        </label>
        {isLogin ? (
          <div className="form-inline">
            <label className="check">
              <input type="checkbox" />
              <span>{t('Ingat saya')}</span>
            </label>
            <button type="button" onClick={() => go('forgotPassword')}>{t('Lupa kata sandi?')}</button>
          </div>
        ) : (
          <label className="check terms">
            <input required type="checkbox" />
            <span>
              {t('Saya menyetujui')} <b>{t('Syarat Penggunaan')}</b> {t('dan')} <b>{t('Kebijakan Privasi')}</b>.
            </span>
          </label>
        )}
        <button className="main-button" type="submit">
              {t(isLogin ? 'Masuk' : 'Buat Akun')} <Icon name="arrow" size={18} />
        </button>
      </form>
      <p className="switch-auth">
        {t(isLogin ? 'Belum punya akun?' : 'Sudah punya akun?')}{' '}
        <button onClick={() => go(isLogin ? 'register' : 'login')}>
          {t(isLogin ? 'Daftar' : 'Masuk')}
        </button>
      </p>
    </div>
  )
}

function AppHeader({ go }: { go: (screen: Screen) => void }) {
  const { t } = useLanguage()
  return (
    <header className="app-header">
      <div>
        <span>{t('Selamat pagi,')}</span>
        <h1>Rizma</h1>
      </div>
      <button className="notification" aria-label="Notifikasi" onClick={() => go('notifications')}>
        <Icon name="bell" />
        <i />
      </button>
    </header>
  )
}

function Home({ go }: { go: (screen: Screen) => void }) {
  const { t } = useLanguage()
  return (
    <AppLayout current="home" go={go}>
      <AppHeader go={go} />
      <section className="streak-card">
        <div className="streak-copy">
          <span>{t('WEEKLY STREAK')}</span>
          <h2>{t('Terus bergerak!')}</h2>
          <p>{t('Kamu sudah aktif 4 hari berturut-turut.')}</p>
        </div>
        <div className="streak-number">
          <Icon name="flame" size={27} />
          <b>4</b>
          <small>{t('HARI')}</small>
        </div>
        <div className="week-row">
          {['S', 'S', 'R', 'K', 'J', 'S', 'M'].map((day, index) => (
            <div key={`${day}-${index}`} className={index < 4 ? 'done' : index === 4 ? 'today' : ''}>
              <i>{index < 4 ? '✓' : ''}</i>
              <span>{day}</span>
            </div>
          ))}
        </div>
      </section>

      <section className="quick-section">
        <div className="section-title">
          <div>
            <span>{t('SIAP BERLATIH?')}</span>
            <h2>{t('Mulai analisis')}</h2>
          </div>
          <button onClick={() => go('analyze')}>
            {t('Lihat semua')} <Icon name="arrow" size={15} />
          </button>
        </div>
        <button className="hero-workout" onClick={() => go('analyze')}>
          <div className="workout-figure">
            <img src={pushupHero} alt="Atlet melakukan gerakan push-up" />
          </div>
          <span className="live-pill"><i /> LIVE AI</span>
          <div className="workout-copy">
            <span>RECOMMENDED</span>
            <h3>{t('Push-up Analysis')}</h3>
            <p>{t('Deteksi sudut siku & repetisi secara real-time')}</p>
            <i className="play-circle"><Icon name="play" size={16} /></i>
          </div>
        </button>
        <div className="exercise-row">
          <button onClick={() => go('analyze')}>
            <span><Icon name="squat" size={28} /></span>
            <b>Squat</b>
            <small>{t('Lower body')}</small>
          </button>
          <button onClick={() => go('analyze')}>
            <span><Icon name="pushup" size={28} /></span>
            <b>Push-up</b>
            <small>{t('Upper body')}</small>
          </button>
          <button onClick={() => go('analyze')}>
            <span><Icon name="situp" size={28} /></span>
            <b>Sit-up</b>
            <small>Core</small>
          </button>
        </div>
      </section>

      <section className="summary-section">
        <div className="section-title">
          <div>
            <span>{t('7 HARI TERAKHIR')}</span>
            <h2>{t('Ringkasan aktivitas')}</h2>
          </div>
        </div>
        <div className="summary-grid">
          <div>
            <span className="summary-icon"><Icon name="clock" size={20} /></span>
            <b>84</b>
            <small>{t('Menit latihan')}</small>
          </div>
          <div>
            <span className="summary-icon"><Icon name="target" size={20} /></span>
            <b>92%</b>
            <small>{t('Akurasi rata-rata')}</small>
          </div>
        </div>
      </section>
    </AppLayout>
  )
}

function Analyze({ go }: { go: (screen: Screen) => void }) {
  const [running, setRunning] = useState(false)
  const [exercise, setExercise] = useState('Push-up')
  const { t, language } = useLanguage()
  const [cameraState, setCameraState] = useState<'intro' | 'requesting' | 'ready' | 'denied'>('intro')
  const videoRef = useRef<HTMLVideoElement>(null)
  const streamRef = useRef<MediaStream | null>(null)

  const enableCamera = async () => {
    setCameraState('requesting')
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: 'user', width: { ideal: 720 }, height: { ideal: 1280 } },
        audio: false,
      })
      streamRef.current = stream
      if (videoRef.current) videoRef.current.srcObject = stream
      setCameraState('ready')
    } catch {
      setCameraState('denied')
    }
  }

  useEffect(() => {
    return () => streamRef.current?.getTracks().forEach((track) => track.stop())
  }, [])

  useEffect(() => {
    if (cameraState === 'ready' && videoRef.current && streamRef.current) {
      videoRef.current.srcObject = streamRef.current
    }
  }, [cameraState])
  return (
    <AppLayout current="analyze" go={go} dark>
      <div className="camera-screen">
        <div className="camera-header">
          <div>
            <span>{t('LIVE ANALYSIS')}</span>
            <i />
          </div>
          <button aria-label="Pengaturan" onClick={() => go('settings')}><Icon name="settings" /></button>
        </div>
        <div className="camera-view">
          {cameraState === 'ready' && <video ref={videoRef} autoPlay muted playsInline className="camera-video" />}
          <div className="frame-corner top-left" />
          <div className="frame-corner top-right" />
          <div className="frame-corner bottom-left" />
          <div className="frame-corner bottom-right" />
          {cameraState === 'requesting' ? (
            <div className="analysis-running">
              <i />
              <b>{t('Menyiapkan kamera...')}</b>
            </div>
          ) : cameraState === 'denied' ? (
            <div className="camera-hint error">
              <Icon name="camera" size={27} />
              <b>{t('Izin kamera ditolak')}</b>
              <span>{t('Aktifkan izin kamera melalui pengaturan perangkat untuk memulai analisis.')}</span>
              <button onClick={enableCamera}>{t('Coba lagi')}</button>
            </div>
          ) : cameraState === 'intro' ? (
            <div className="camera-permission">
              <span><Icon name="camera" size={25} /></span>
              <small>{t('AKSES KAMERA')}</small>
              <h2>{t('Kamera digunakan hanya untuk menganalisis gerakanmu.')}</h2>
              <p>{t('Video tidak disimpan kecuali kamu mengaktifkan penyimpanan melalui Pengaturan.')}</p>
              <button onClick={enableCamera}>{t('Izinkan kamera')}</button>
            </div>
          ) : running ? (
            <div className="analysis-running">
              <i />
              <b>{language === 'en' ? 'Analyzing movement' : 'Menganalisis gerakan'}</b>
              <span>{language === 'en' ? 'Keep your entire body inside the frame' : 'Pastikan seluruh tubuh tetap di dalam bingkai'}</span>
            </div>
          ) : (
            <div className="camera-hint">
              <Icon name="camera" size={27} />
              <b>{t('Kamera siap')}</b>
              <span>{t('Seluruh tubuh harus terlihat di dalam bingkai.')}</span>
            </div>
          )}
        </div>
        <div className="analysis-panel">
          <div className="exercise-select">
            <span>
              <small>{t('JENIS LATIHAN')}</small>
              <b>{t(exercise)}</b>
            </span>
            <Icon name="chevronDown" size={18} />
          </div>
          <div className="exercise-choices">
            {['Push-up', 'Sit-up', 'Squat'].map((item) => (
              <button
                key={item}
                className={exercise === item ? 'active' : ''}
                onClick={() => setExercise(item)}
              >
                {t(item)}
              </button>
            ))}
          </div>
          {running && (
            <>
              <div className="posture-feedback good">
                <i>✓</i><div><b>{t('Postur baik')}</b><span>{t('Gerakan stabil dan siap dihitung.')}</span></div>
              </div>
              <div className="live-metrics">
                <div><small>{t('REPETISI')}</small><b>12</b></div>
                <div><small>{t('KEDALAMAN')}</small><b>86%</b></div>
                <div><small>{t('POSTUR')}</small><b className="good">{t('Baik')}</b></div>
              </div>
            </>
          )}
          <button
            className={`record-button ${running ? 'stop' : ''}`}
            onClick={() => cameraState === 'ready' ? setRunning(!running) : enableCamera()}
            disabled={cameraState === 'requesting'}
          >
            <i>{running ? <span /> : <Icon name="play" size={19} />}</i>
            {t(running ? 'Selesai Analisis' : 'Mulai Analisis')}
          </button>
        </div>
      </div>
    </AppLayout>
  )
}

const sessions = [
  { type: 'Squat', date: 'Hari ini, 08:24', reps: '24 reps', score: 94, icon: 'squat' },
  { type: 'Push-up', date: 'Kemarin, 17:10', reps: '18 reps', score: 88, icon: 'pushup' },
  { type: 'Sit-up', date: '24 Feb, 07:45', reps: '22 reps', score: 91, icon: 'situp' },
  { type: 'Squat', date: '22 Feb, 18:30', reps: '30 reps', score: 86, icon: 'squat' },
]

function History({
  go,
  openSession,
}: {
  go: (screen: Screen) => void
  openSession: (session: (typeof sessions)[number]) => void
}) {
  const [filterOpen, setFilterOpen] = useState(false)
  const [filter, setFilter] = useState('Semua')
  const [selectedBar, setSelectedBar] = useState(5)
  const { t } = useLanguage()
  const visibleSessions = filter === 'Semua' ? sessions : sessions.filter((session) => session.type === filter)
  const overviewData = [2, 4, 3, 6, 4, 8, 5]
  return (
    <AppLayout current="history" go={go}>
      <div className="page-mobile-head">
        <span>{t('PROGRES LATIHAN')}</span>
        <h1>{t('Riwayat')}</h1>
      </div>
      <section
        className="history-overview interactive"
        role="button"
        tabIndex={0}
        onClick={() => go('analytics')}
        onKeyDown={(event) => event.key === 'Enter' && go('analytics')}
      >
        <div>
          <small>{t('FEBRUARI 2026')}</small>
          <b>{t('8 sesi')}</b>
          <span>{t('+24% dari Januari')}</span>
          <em>{t('Lihat statistik lengkap')} <Icon name="arrow" size={12} /></em>
        </div>
        <div className="mini-bars">
          {overviewData.map((value, index) => (
            <button
              key={index}
              style={{ height: `${value * 11}%` }}
              className={selectedBar === index ? 'peak' : ''}
              onClick={(event) => {
                event.stopPropagation()
                setSelectedBar(index)
              }}
              aria-label={`${value} ${t('sesi')}`}
            >
              {selectedBar === index && <span>{value}</span>}
            </button>
          ))}
        </div>
      </section>
      <div className="history-title">
        <h2>{t('Aktivitas terbaru')}</h2>
        <button onClick={() => setFilterOpen(!filterOpen)}>
          {filter === 'Semua' ? t('Filter') : t(filter)}
        </button>
      </div>
      {filterOpen && (
        <div className="filter-row">
          {['Semua', 'Push-up', 'Sit-up', 'Squat'].map((item) => (
            <button
              key={item}
              className={filter === item ? 'active' : ''}
              onClick={() => {
                setFilter(item)
                setFilterOpen(false)
              }}
            >
              {t(item)}
            </button>
          ))}
        </div>
      )}
      <div className="session-list">
        {visibleSessions.map((session, index) => (
          <button className="session-item" key={`${session.date}-${index}`} onClick={() => openSession(session)}>
            <span className="session-icon"><Icon name={session.icon} size={25} /></span>
            <div>
              <h3>{t(session.type)}</h3>
              <p>{t(session.date)} · {session.reps}</p>
            </div>
            <span className="score">
              <b>{session.score}</b>
              <small>{t('SKOR')}</small>
            </span>
            <Icon name="arrow" size={16} />
          </button>
        ))}
      </div>
    </AppLayout>
  )
}

function Analytics({ go }: { go: (screen: Screen) => void }) {
  const { t } = useLanguage()
  const [period, setPeriod] = useState<'Minggu' | 'Bulan' | '3 Bulan'>('Bulan')
  const datasets = {
    Minggu: [2, 3, 1, 4, 3, 5, 4],
    Bulan: [3, 5, 4, 7, 5, 8, 6, 9],
    '3 Bulan': [12, 18, 24],
  }
  const labels = {
    Minggu: ['S', 'S', 'R', 'K', 'J', 'S', 'M'],
    Bulan: ['1', '5', '9', '13', '17', '21', '25', '28'],
    '3 Bulan': ['Des', 'Jan', 'Feb'],
  }
  const data = datasets[period]
  const [selected, setSelected] = useState(5)
  const activeIndex = Math.min(selected, data.length - 1)
  const maxValue = Math.max(...data)

  const changePeriod = (next: 'Minggu' | 'Bulan' | '3 Bulan') => {
    setPeriod(next)
    setSelected(next === '3 Bulan' ? 2 : next === 'Minggu' ? 6 : 5)
  }

  return (
    <DetailLayout title="Statistik latihan" eyebrow="DETAIL AKTIVITAS" back={() => go('history')}>
      <div className="analytics-periods">
        {(['Minggu', 'Bulan', '3 Bulan'] as const).map((item) => (
          <button key={item} className={period === item ? 'active' : ''} onClick={() => changePeriod(item)}>
            {t(item)}
          </button>
        ))}
      </div>
      <section className="analytics-chart">
        <div className="chart-heading">
          <div><span>{t('Aktivitas latihan')}</span><b>{data.reduce((sum, value) => sum + value, 0)} {t('sesi')}</b></div>
          <div className="chart-value"><b>{data[activeIndex]}</b><span>{labels[period][activeIndex]}</span></div>
        </div>
        <div className="chart-area">
          <div className="chart-lines"><i /><i /><i /></div>
          {data.map((value, index) => (
            <button
              key={`${period}-${index}`}
              className={activeIndex === index ? 'active' : ''}
              style={{ height: `${Math.max(14, (value / maxValue) * 100)}%` }}
              onClick={() => setSelected(index)}
            >
              <i />
              <span>{labels[period][index]}</span>
            </button>
          ))}
        </div>
      </section>
      <section className="analytics-metrics">
        <div><span>{t('Total latihan')}</span><b>8</b><small>+24%</small></div>
        <div><span>{t('Total waktu')}</span><b>84</b><small>{t('menit')}</small></div>
        <div><span>{t('Rata-rata skor')}</span><b>91%</b><small>+3%</small></div>
        <div><span>{t('Repetisi bersih')}</span><b>164</b><small>92%</small></div>
      </section>
      <section className="exercise-breakdown">
        <h3>{t('JENIS LATIHAN')}</h3>
        {[
          ['Push-up', 42, '74 reps'],
          ['Squat', 35, '68 reps'],
          ['Sit-up', 23, '42 reps'],
        ].map(([name, width, value]) => (
          <div key={name as string}>
            <span><b>{name}</b><small>{value}</small></span>
            <i><em style={{ width: `${width}%` }} /></i>
          </div>
        ))}
      </section>
    </DetailLayout>
  )
}

function Profile({ go }: { go: (screen: Screen) => void }) {
  const { t } = useLanguage()
  return (
    <AppLayout current="profile" go={go}>
      <div className="page-mobile-head profile-head">
        <span>{t('AKUN SAYA')}</span>
        <h1>{t('Profil')}</h1>
      </div>
      <section className="profile-card">
        <div className="profile-avatar">RI</div>
        <h2>Rizma Indra Pramudya</h2>
        <p>rizma@unesa.ac.id</p>
        <span>{t('MEMBER SEJAK 2026')}</span>
      </section>
      <section className="profile-stats">
        <div><b>32</b><span>{t('Total sesi')}</span></div>
        <div><b>486</b><span>{t('Total reps')}</span></div>
        <div><b>91%</b><span>{t('Avg. skor')}</span></div>
      </section>
      <section className="menu-list">
        <button onClick={() => go('editProfile')}><span><Icon name="user" /></span><b>{t('Edit profil')}</b><Icon name="arrow" size={17} /></button>
        <button onClick={() => go('settings')}><span><Icon name="settings" /></span><b>{t('Pengaturan aplikasi')}</b><Icon name="arrow" size={17} /></button>
        <button onClick={() => go('help')}><span><Icon name="help" /></span><b>{t('Bantuan SKELIO')}</b><Icon name="arrow" size={17} /></button>
        <button onClick={() => go('about')}><span><Icon name="users" /></span><b>{t('Tentang kami')}</b><Icon name="arrow" size={17} /></button>
        <button className="logout" onClick={() => go('welcome')}><span><Icon name="logout" /></span><b>{t('Keluar')}</b></button>
      </section>
      <p className="app-version">SKELIO v1.0 · UNESA 2026</p>
    </AppLayout>
  )
}

function DetailLayout({
  title,
  eyebrow,
  back,
  children,
}: {
  title: string
  eyebrow: string
  back: () => void
  children: ReactNode
}) {
  const { t } = useLanguage()
  return (
    <div className="plain-screen detail-screen">
      <StatusBar />
      <header className="detail-header">
        <button className="round-back" onClick={back} aria-label="Kembali">
          <Icon name="back" size={20} />
        </button>
        <div>
          <span>{t(eyebrow)}</span>
          <h1>{t(title)}</h1>
        </div>
      </header>
      <div className="detail-content">{children}</div>
    </div>
  )
}

function ForgotPassword({ go }: { go: (screen: Screen) => void }) {
  const [sent, setSent] = useState(false)
  const { t } = useLanguage()
  return (
    <DetailLayout title="Atur ulang sandi" eyebrow="BANTUAN AKUN" back={() => go('login')}>
      {sent ? (
        <div className="action-success">
          <span>✓</span>
          <h2>{t('Periksa emailmu')}</h2>
          <p>{t('Tautan untuk mengatur ulang kata sandi telah dikirim ke email yang kamu masukkan.')}</p>
          <button className="main-button" onClick={() => go('login')}>{t('Kembali ke login')}</button>
        </div>
      ) : (
        <>
          <p className="detail-intro">{t('Masukkan email akun SKELIO. Kami akan mengirimkan tautan pemulihan kata sandi.')}</p>
          <form className="mobile-form compact-form" onSubmit={(event) => { event.preventDefault(); setSent(true) }}>
            <label>
              <span>Email</span>
              <div className="input-wrap">
                <Icon name="mail" size={19} />
                <input required type="email" placeholder="nama@email.com" />
              </div>
            </label>
            <button className="main-button" type="submit">{t('Kirim tautan pemulihan')}</button>
          </form>
        </>
      )}
    </DetailLayout>
  )
}

function Notifications({
  go,
  openSession,
}: {
  go: (screen: Screen) => void
  openSession: (session: (typeof sessions)[number]) => void
}) {
  const { t } = useLanguage()
  const notices = [
    ['Analisis selesai', 'Skor Push-up kamu hari ini mencapai 94. Lihat detail hasil latihan.', 'Baru saja'],
    ['Target mingguan', 'Satu sesi lagi untuk menyelesaikan target latihan minggu ini.', '2 jam lalu'],
    ['Tips postur', 'Jaga posisi pinggul tetap sejajar saat melakukan Push-up.', 'Kemarin'],
  ]
  return (
    <DetailLayout title="Notifikasi" eyebrow="PEMBARUAN" back={() => go('home')}>
      <div className="notification-list">
        {notices.map(([title, text, time], index) => (
          <button
            key={title}
            className={index === 0 ? 'unread' : ''}
            onClick={() => index === 0 ? openSession(sessions[0]) : index === 1 ? go('home') : go('help')}
          >
            <i />
            <div><h3>{t(title)}</h3><p>{t(text)}</p><span>{t(time)}</span></div>
            <Icon name="arrow" size={16} />
          </button>
        ))}
      </div>
    </DetailLayout>
  )
}

function SessionDetail({
  go,
  session,
}: {
  go: (screen: Screen) => void
  session: (typeof sessions)[number]
}) {
  const { t } = useLanguage()
  return (
    <DetailLayout title="Hasil analisis" eyebrow={`${t(session.type).toUpperCase()} · ${t(session.date).toUpperCase()}`} back={() => go('history')}>
      <section className="result-score">
        <div className="score-ring"><b>{session.score}</b><span>{t('SKOR')}</span></div>
        <div><span>{t('POSTUR KESELURUHAN')}</span><h2>{t('Sangat baik')}</h2><p>{t('Gerakan stabil dan kedalaman repetisi konsisten.')}</p></div>
      </section>
      <section className="result-metrics">
        <div><span>{t('REPETISI')}</span><b>{session.reps.split(' ')[0]}</b><small>{t(session.reps.includes('reps') ? 'Clean reps tercatat' : 'Durasi tertahan')}</small></div>
        <div><span>{t('DURASI')}</span><b>02:18</b><small>{t('Waktu aktif')}</small></div>
        <div><span>{t('AKURASI')}</span><b>94%</b><small>{t('+3% dari sesi lalu')}</small></div>
        <div><span>{t('SUDUT SIKU')}</span><b>89°</b><small>{t('Rentang optimal')}</small></div>
      </section>
      <section className="feedback-card">
        <span>{t('FEEDBACK AI')}</span>
        <h3>{t('Pertahankan posisi tubuhmu')}</h3>
        <p>{t('Postur bahu dan pinggul sudah sejajar. Pada dua repetisi terakhir, usahakan siku tidak terlalu melebar untuk menjaga beban tetap stabil.')}</p>
      </section>
      <button className="main-button" onClick={() => go('analyze')}>{t('Ulangi latihan')}</button>
    </DetailLayout>
  )
}

function EditProfile({ go }: { go: (screen: Screen) => void }) {
  const [saved, setSaved] = useState(false)
  const [photoName, setPhotoName] = useState('')
  const { t } = useLanguage()
  return (
    <DetailLayout title="Edit profil" eyebrow="INFORMASI PRIBADI" back={() => go('profile')}>
      <div className="edit-avatar">
        <div>RI</div>
        <label>
          {photoName || t('Ubah foto')}
          <input type="file" accept="image/*" onChange={(event) => setPhotoName(event.target.files?.[0]?.name || '')} />
        </label>
      </div>
      <form className="mobile-form compact-form" onSubmit={(event) => { event.preventDefault(); setSaved(true) }}>
        <label><span>{t('Nama lengkap')}</span><div className="input-wrap"><Icon name="user" size={19} /><input required defaultValue="Rizma Indra Pramudya" /></div></label>
        <label><span>Email</span><div className="input-wrap"><Icon name="mail" size={19} /><input required type="email" defaultValue="rizma@unesa.ac.id" /></div></label>
        <label><span>{t('Program studi')}</span><div className="input-wrap text-input"><input defaultValue="S1 Teknik Informatika" /></div></label>
        {saved && <p className="saved-message">{t('Perubahan profil berhasil disimpan.')}</p>}
        <button className="main-button" type="submit">{t('Simpan perubahan')}</button>
      </form>
    </DetailLayout>
  )
}

function ToggleRow({ title, text, initial = true }: { title: string; text: string; initial?: boolean }) {
  const [enabled, setEnabled] = useState(initial)
  const { t } = useLanguage()
  return (
    <button className="toggle-row" onClick={() => setEnabled(!enabled)}>
      <div><b>{t(title)}</b><span>{t(text)}</span></div>
      <i className={enabled ? 'enabled' : ''}><span /></i>
    </button>
  )
}

function Settings({ go, backTo }: { go: (screen: Screen) => void; backTo: Screen }) {
  const { language, setLanguage, t } = useLanguage()
  return (
    <DetailLayout title="Pengaturan" eyebrow="PREFERENSI APLIKASI" back={() => go(backTo)}>
      <div className="settings-group">
        <span>{t('ANALISIS')}</span>
        <ToggleRow title="Suara feedback" text="Instruksi suara selama latihan" />
        <ToggleRow title="Getaran" text="Getaran saat repetisi tervalidasi" />
        <ToggleRow title="Simpan video" text="Simpan rekaman analisis otomatis" initial={false} />
      </div>
      <div className="settings-group">
        <span>{t('NOTIFIKASI')}</span>
        <ToggleRow title="Pengingat latihan" text="Pengingat target mingguan" />
        <ToggleRow title="Tips postur" text="Rekomendasi berdasarkan hasil latihan" />
      </div>
      <button className="settings-select" onClick={() => setLanguage(language === 'id' ? 'en' : 'id')}>
        <div><b>{t('Bahasa')}</b><span>{language === 'id' ? 'Bahasa Indonesia' : 'English'}</span></div><Icon name="arrow" size={17} />
      </button>
    </DetailLayout>
  )
}

function Help({ go }: { go: (screen: Screen) => void }) {
  const [open, setOpen] = useState<number | null>(0)
  const { t } = useLanguage()
  const questions = [
    ['Bagaimana memulai analisis?', 'Pilih menu Analisis, tentukan Push-up, Sit-up, atau Squat, lalu posisikan seluruh tubuh di dalam bingkai kamera.'],
    ['Mengapa repetisi tidak terhitung?', 'Pastikan pencahayaan cukup dan gerakan mencapai ambang kedalaman yang ditentukan.'],
    ['Apakah video saya disimpan?', 'Video tidak disimpan secara otomatis kecuali opsi Simpan video diaktifkan pada Pengaturan.'],
  ]
  return (
    <DetailLayout title="Bantuan" eyebrow="PUSAT INFORMASI" back={() => go('profile')}>
      <section className="about-card">
        <Logo />
        <div><h2>SKELIO</h2><p>Real-Time Biomechanical Analysis Pipeline</p></div>
      </section>
      <h3 className="faq-title">{t('Pertanyaan umum')}</h3>
      <div className="faq-list">
        {questions.map(([question, answer], index) => (
          <button key={question} className={open === index ? 'open' : ''} onClick={() => setOpen(open === index ? null : index)}>
            <div><b>{t(question)}</b><Icon name="chevronDown" size={17} /></div>
            {open === index && <p>{t(answer)}</p>}
          </button>
        ))}
      </div>
      <a className="contact-card" href="mailto:skelio@unesa.ac.id">
        <Icon name="mail" />
        <div><b>{t('Hubungi tim SKELIO')}</b><span>{t('Kelompok 11 Big Data UNESA')}</span></div>
        <Icon name="arrow" size={17} />
      </a>
    </DetailLayout>
  )
}

const teamMembers = [
  { name: 'Rizma Indra Pramudya', nim: '25051204370', initials: 'RI' },
  { name: 'Izora Elverda Narulita Putri', nim: '25051204287', initials: 'IE' },
  { name: 'Putera Al Khalidi', nim: '25051204362', initials: 'PA' },
  { name: "Muhammad Abdullah Ro'in", nim: '25051204270', initials: 'MR' },
]

function About({ go }: { go: (screen: Screen) => void }) {
  const { t } = useLanguage()
  return (
    <DetailLayout title="Tentang kami" eyebrow="TIM PENGEMBANG" back={() => go('profile')}>
      <section className="about-hero">
        <Logo />
        <div>
          <h2>{t('Tim di balik SKELIO')}</h2>
          <p>{t('SKELIO merupakan proyek Kelompok 11 untuk mata kuliah Big Data, Program Studi S1 Teknik Informatika, Universitas Negeri Surabaya.')}</p>
        </div>
      </section>
      <div className="team-section-title">
        <span>{t('ANGGOTA TIM')}</span>
      </div>
      <section className="member-list">
        {teamMembers.map((member) => (
          <article className="member-card" key={member.nim}>
            <div className="member-avatar">{member.initials}</div>
            <div className="member-info">
              <h3>{member.name}</h3>
              <p>NIM {member.nim}</p>
            </div>
          </article>
        ))}
      </section>
      <div className="advisor-card">
        <div>SY</div>
        <span><small>{t('Dosen pembimbing')}</small><b>Saifudin Yahya, S.Kom., M.T.I</b></span>
      </div>
      <div className="unesa-note">
        <div>
          <b>{t('Kelompok 11 · Big Data')}</b>
          <p>Universitas Negeri Surabaya</p>
        </div>
        <span>2026</span>
      </div>
    </DetailLayout>
  )
}

function BottomNav({ current, go, dark = false }: { current: Screen; go: (s: Screen) => void; dark?: boolean }) {
  const { t } = useLanguage()
  const items = [
    ['home', 'home', 'Beranda'],
    ['analyze', 'scan', 'Analisis'],
    ['history', 'history', 'Riwayat'],
    ['profile', 'user', 'Profil'],
  ]
  return (
    <nav className={`bottom-nav ${dark ? 'dark' : ''}`} aria-label="Navigasi aplikasi">
      {items.map(([screen, icon, label]) => (
        <button key={screen} className={current === screen ? 'active' : ''} onClick={() => go(screen as Screen)}>
          <span><Icon name={icon} size={21} /></span>
          <small>{t(label)}</small>
        </button>
      ))}
    </nav>
  )
}

function AppLayout({
  current,
  go,
  children,
  dark = false,
}: {
  current: Screen
  go: (s: Screen) => void
  children: ReactNode
  dark?: boolean
}) {
  return (
    <div className={`main-app-screen ${dark ? 'dark-screen' : ''}`}>
      <StatusBar light={dark} />
      <div className="scroll-content">{children}</div>
      <BottomNav current={current} go={go} dark={dark} />
    </div>
  )
}

export default function App() {
  const [screen, setScreen] = useState<Screen>('welcome')
  const [previousScreen, setPreviousScreen] = useState<Screen>('home')
  const [selectedSession, setSelectedSession] = useState(sessions[0])
  const [language, setLanguage] = useState<Language>('id')
  const go = (next: Screen) => {
    setPreviousScreen(screen)
    setScreen(next)
    document.querySelector('.scroll-content')?.scrollTo({ top: 0 })
  }
  const openSession = (session: (typeof sessions)[number]) => {
    setSelectedSession(session)
    go('sessionDetail')
  }
  return (
    <LanguageContext.Provider value={{ language, setLanguage }}>
      <div className="mobile-stage">
        <div className="phone-app">
          {screen === 'welcome' && <Welcome go={go} />}
          {screen === 'login' && <AuthScreen mode="login" go={go} />}
          {screen === 'register' && <AuthScreen mode="register" go={go} />}
          {screen === 'forgotPassword' && <ForgotPassword go={go} />}
          {screen === 'home' && <Home go={go} />}
          {screen === 'analyze' && <Analyze go={go} />}
          {screen === 'history' && <History go={go} openSession={openSession} />}
          {screen === 'analytics' && <Analytics go={go} />}
          {screen === 'sessionDetail' && <SessionDetail go={go} session={selectedSession} />}
          {screen === 'profile' && <Profile go={go} />}
          {screen === 'notifications' && <Notifications go={go} openSession={openSession} />}
          {screen === 'editProfile' && <EditProfile go={go} />}
          {screen === 'settings' && <Settings go={go} backTo={previousScreen === 'analyze' ? 'analyze' : 'profile'} />}
          {screen === 'help' && <Help go={go} />}
          {screen === 'about' && <About go={go} />}
        </div>
      </div>
    </LanguageContext.Provider>
  )
}
