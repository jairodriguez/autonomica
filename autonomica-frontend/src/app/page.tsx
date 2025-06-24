'use client';

import ChatContainerAI from '@/components/chat-container-ai';
import Layout from '@/components/layout';
import { SignInButton, UserButton } from '@/components';
import { useUser } from '@clerk/nextjs';
import Link from 'next/link';
import { Message } from '@/types/chat';

export default function HomePage() {
  const { isLoaded, isSignedIn } = useUser();

  return (
    <Layout>
      <div className="min-h-screen bg-gray-900 px-4 sm:px-0">
        {/* Navigation Bar */}
        <div className="flex justify-between items-center py-6 mb-8">
          <div className="flex items-center space-x-2">
            <h1 className="text-2xl font-bold text-white">Autonomica</h1>
          </div>
          <div className="flex items-center space-x-4">
            {isLoaded && (
              <>
                {isSignedIn ? (
                  <UserButton />
                ) : (
                  <SignInButton />
                )}
              </>
            )}
          </div>
        </div>

        {/* Hero Section */}
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-gray-100 mb-4">
            Autonomica Marketing AI
          </h1>
          <p className="text-xl text-gray-300 max-w-3xl mx-auto mb-2">
            Powered by OWL (Optimized Workflow Language) and CAMEL multi-agent systems
          </p>
          <p className="text-lg text-gray-400 max-w-2xl mx-auto mb-6">
            Get intelligent marketing insights, content creation, SEO analysis, and campaign planning 
            from your AI-powered marketing team.
          </p>
          
          {/* Navigation to Projects */}
          <div className="flex justify-center space-x-4 mb-8">
            {isSignedIn ? (
              <>
                <Link 
                  href="/projects"
                  className="inline-flex items-center px-6 py-3 border border-transparent text-base font-medium rounded-md text-white bg-purple-600 hover:bg-purple-700 transition-colors"
                >
                  🏗️ Manage Projects & Agents
                </Link>
                <Link 
                  href="/dashboard"
                  className="inline-flex items-center px-6 py-3 border border-gray-600 text-base font-medium rounded-md text-gray-300 bg-gray-800 hover:bg-gray-700 transition-colors"
                >
                  📊 Analytics Dashboard
                </Link>
              </>
            ) : (
              <div className="space-x-4">
                <div className="inline-flex items-center px-6 py-3 border border-gray-600 text-base font-medium rounded-md text-gray-400 bg-gray-700 cursor-not-allowed">
                  🔒 Sign in to Manage Projects
                </div>
                <div className="inline-flex items-center px-6 py-3 border border-gray-600 text-base font-medium rounded-md text-gray-400 bg-gray-700 cursor-not-allowed">
                  🔒 Sign in for Dashboard
                </div>
              </div>
            )}
            <button className="inline-flex items-center px-6 py-3 border border-gray-600 text-base font-medium rounded-md text-gray-300 bg-gray-800 hover:bg-gray-700 transition-colors">
              💬 Quick Chat Below
            </button>
          </div>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          <div className="bg-gray-800 rounded-lg border border-gray-700 p-6 text-center">
            <div className="text-3xl font-bold text-purple-400 mb-2">🎯</div>
            <h3 className="text-lg font-medium text-gray-100 mb-1">Strategy</h3>
            <p className="text-sm text-gray-400">Marketing strategy and campaign planning</p>
          </div>
          <div className="bg-gray-800 rounded-lg border border-gray-700 p-6 text-center">
            <div className="text-3xl font-bold text-green-400 mb-2">📝</div>
            <h3 className="text-lg font-medium text-gray-100 mb-1">Content</h3>
            <p className="text-sm text-gray-400">AI-powered content creation and optimization</p>
          </div>
          <div className="bg-gray-800 rounded-lg border border-gray-700 p-6 text-center">
            <div className="text-3xl font-bold text-blue-400 mb-2">📊</div>
            <h3 className="text-lg font-medium text-gray-100 mb-1">Analytics</h3>
            <p className="text-sm text-gray-400">Performance insights and data analysis</p>
          </div>
        </div>

        {/* Main Chat Interface */}
        <div className="bg-gray-800 rounded-lg border border-gray-700 shadow-sm mb-8">
          <div className="h-[600px]">
            <ChatContainerAI 
              className="h-full"
              onFinish={(message: Message) => {
                console.log('Message completed:', message);
              }}
              onError={(error: Error) => {
                console.error('Chat error:', error);
              }}
            />
          </div>
        </div>

        {/* Quick Actions */}
        <div className="bg-gray-800 rounded-lg border border-gray-700 p-6">
          <h2 className="text-lg font-medium text-gray-100 mb-4">Try these examples:</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="bg-gray-700 rounded-lg p-4 border border-gray-600 cursor-pointer hover:bg-gray-600 transition-colors">
              <h3 className="font-medium text-gray-100 mb-2">💡 Marketing Strategy</h3>
              <p className="text-sm text-gray-300">&ldquo;Help me create a marketing strategy for a new SaaS product targeting small businesses&rdquo;</p>
            </div>
            <div className="bg-gray-700 rounded-lg p-4 border border-gray-600 cursor-pointer hover:bg-gray-600 transition-colors">
              <h3 className="font-medium text-gray-100 mb-2">🔍 SEO Analysis</h3>
              <p className="text-sm text-gray-300">&ldquo;What are the best keywords for content marketing in 2024?&rdquo;</p>
            </div>
            <div className="bg-gray-700 rounded-lg p-4 border border-gray-600 cursor-pointer hover:bg-gray-600 transition-colors">
              <h3 className="font-medium text-gray-100 mb-2">📱 Social Media</h3>
              <p className="text-sm text-gray-300">&ldquo;Create a social media content calendar for a tech startup&rdquo;</p>
            </div>
            <div className="bg-gray-700 rounded-lg p-4 border border-gray-600 cursor-pointer hover:bg-gray-600 transition-colors">
              <h3 className="font-medium text-gray-100 mb-2">📊 Analytics</h3>
              <p className="text-sm text-gray-300">&ldquo;How do I measure the ROI of my content marketing efforts?&rdquo;</p>
            </div>
          </div>
        </div>
      </div>
    </Layout>
  );
}
