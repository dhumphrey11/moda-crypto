import { ReactNode } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/router';
import { useAuth } from '../lib/useAuth';

interface LayoutProps {
    children: ReactNode;
}

const Layout = ({ children }: LayoutProps) => {
    const router = useRouter();
    const { user, logout } = useAuth();

    const navigation = [
        { name: 'Dashboard', href: '/', icon: '📊' },
        { name: 'Signals', href: '/signals', icon: '📡' },
        { name: 'Portfolio', href: '/portfolio', icon: '💼' },
        { name: 'Watchlist', href: '/watchlist', icon: '👀' },
        { name: 'Admin', href: '/admin', icon: '⚙️' },
    ];

    const handleLogout = async () => {
        try {
            await logout();
            router.push('/login');
        } catch (error) {
            console.error('Logout failed:', error);
        }
    };

    return (
        <div className="min-h-screen bg-gray-50">
            {/* Navigation */}
            <nav className="bg-slate-800 shadow-lg border-b border-slate-700">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                    <div className="flex justify-between h-16">
                        <div className="flex">
                            {/* Logo */}
                            <div className="flex-shrink-0 flex items-center">
                                <Link href="/" className="text-xl font-bold text-white hover:text-primary-300 transition-colors">
                                    Moda Crypto
                                </Link>
                            </div>

                            {/* Navigation Links */}
                            <div className="hidden sm:ml-6 sm:flex sm:space-x-8">
                                {navigation.map((item) => {
                                    const isActive = router.pathname === item.href;
                                    return (
                                        <Link
                                            key={item.name}
                                            href={item.href}
                                            className={`inline-flex items-center px-1 pt-1 border-b-2 text-sm font-medium transition-colors ${isActive
                                                ? 'border-primary-400 text-white'
                                                : 'border-transparent text-gray-300 hover:border-gray-500 hover:text-white'
                                                }`}
                                        >
                                            <span className="mr-2">{item.icon}</span>
                                            {item.name}
                                        </Link>
                                    );
                                })}
                            </div>
                        </div>

                        {/* User Menu */}
                        <div className="flex items-center">
                            <div className="flex-shrink-0">
                                <div className="relative">
                                    <div className="flex items-center space-x-4">
                                        {/* User Info */}
                                        <div className="text-sm">
                                            <div className="font-medium text-white">{user?.email}</div>
                                            <div className="text-gray-300">Administrator</div>
                                        </div>

                                        {/* User Avatar */}
                                        <div className="h-8 w-8 rounded-full bg-primary-600 flex items-center justify-center">
                                            <span className="text-white font-medium">
                                                {user?.email?.charAt(0).toUpperCase()}
                                            </span>
                                        </div>

                                        {/* Logout Button */}
                                        <button
                                            onClick={handleLogout}
                                            className="text-gray-300 hover:text-white focus:outline-none focus:text-white transition-colors"
                                            title="Logout"
                                        >
                                            <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
                                            </svg>
                                        </button>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                {/* Mobile Navigation */}
                <div className="sm:hidden">
                    <div className="pt-2 pb-3 space-y-1">
                        {navigation.map((item) => {
                            const isActive = router.pathname === item.href;
                            return (
                                <Link
                                    key={item.name}
                                    href={item.href}
                                    className={`block pl-3 pr-4 py-2 border-l-4 text-base font-medium transition-colors ${isActive
                                        ? 'bg-slate-700 border-primary-400 text-white'
                                        : 'border-transparent text-gray-300 hover:bg-slate-700 hover:border-gray-500 hover:text-white'
                                        }`}
                                >
                                    <span className="mr-2">{item.icon}</span>
                                    {item.name}
                                </Link>
                            );
                        })}
                    </div>
                </div>
            </nav>

            {/* Main Content */}
            <main className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
                <div className="px-4 py-6 sm:px-0">
                    {children}
                </div>
            </main>

            {/* Footer */}
            <footer className="bg-slate-800 border-t border-slate-700 mt-12">
                <div className="max-w-7xl mx-auto py-4 px-4 sm:px-6 lg:px-8">
                    <div className="flex justify-between items-center">
                        <div className="text-sm text-gray-300">
                            © 2025 Moda Crypto. Built with Next.js and FastAPI.
                        </div>
                        <div className="flex space-x-6">
                            <a href="#" className="text-sm text-gray-300 hover:text-white transition-colors">
                                GitHub
                            </a>
                            <a href="#" className="text-sm text-gray-300 hover:text-white transition-colors">
                                Documentation
                            </a>
                        </div>
                    </div>
                </div>
            </footer>
        </div>
    );
};

export default Layout;