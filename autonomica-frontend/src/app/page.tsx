'use client';

import { ChatContainerAI, Layout } from '@/components';
import Link from 'next/link';

export default function HomePage() {
  return (
    <Layout>
      <div className="px-4 sm:px-0">
        {/* Hero Section */}
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-gray-900 mb-4">
            Autonomica Marketing AI
          </h1>
          <p className="text-xl text-gray-600 max-w-3xl mx-auto mb-2">
            Powered by OWL (Optimized Workflow Language) and CAMEL multi-agent systems
          </p>
          <p className="text-lg text-gray-500 max-w-2xl mx-auto mb-6">
            Get intelligent marketing insights, content creation, SEO analysis, and campaign planning 
            from your AI-powered marketing team.
          </p>
          
          {/* Navigation to Projects */}
          <div className="flex justify-center space-x-4 mb-8">
            <Link 
              href="/projects"
              className="inline-flex items-center px-6 py-3 border border-transparent text-base font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 transition-colors"
            >
              🏗️ Manage Projects & Agents
            </Link>
            <button className="inline-flex items-center px-6 py-3 border border-gray-300 text-base font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 transition-colors">
              💬 Quick Chat Below
            </button>
          </div>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          <div className="bg-white rounded-lg border p-6 text-center">
            <div className="text-3xl font-bold text-blue-600 mb-2">🎯</div>
            <h3 className="text-lg font-medium text-gray-900 mb-1">Strategy</h3>
            <p className="text-sm text-gray-500">Marketing strategy and campaign planning</p>
          </div>
          <div className="bg-white rounded-lg border p-6 text-center">
            <div className="text-3xl font-bold text-green-600 mb-2">📝</div>
            <h3 className="text-lg font-medium text-gray-900 mb-1">Content</h3>
            <p className="text-sm text-gray-500">AI-powered content creation and optimization</p>
          </div>
          <div className="bg-white rounded-lg border p-6 text-center">
            <div className="text-3xl font-bold text-purple-600 mb-2">📊</div>
            <h3 className="text-lg font-medium text-gray-900 mb-1">Analytics</h3>
            <p className="text-sm text-gray-500">Performance insights and data analysis</p>
          </div>
        </div>

        {/* Main Chat Interface */}
        <div className="bg-white rounded-lg border shadow-sm mb-8">
          <div className="h-[600px]">
            <ChatContainerAI 
              className="h-full"
              onFinish={(message) => {
                console.log('Message completed:', message);
              }}
              onError={(error) => {
                console.error('Chat error:', error);
              }}
            />
          </div>
        </div>

        {/* Quick Actions */}
        <div className="bg-gray-50 rounded-lg p-6">
          <h2 className="text-lg font-medium text-gray-900 mb-4">Try these examples:</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="bg-white rounded-lg p-4 border cursor-pointer hover:shadow-md transition-shadow">
              <h3 className="font-medium text-gray-900 mb-2">💡 Marketing Strategy</h3>
              <p className="text-sm text-gray-600">&ldquo;Help me create a marketing strategy for a new SaaS product targeting small businesses&rdquo;</p>
            </div>
            <div className="bg-white rounded-lg p-4 border cursor-pointer hover:shadow-md transition-shadow">
              <h3 className="font-medium text-gray-900 mb-2">🔍 SEO Analysis</h3>
              <p className="text-sm text-gray-600">&ldquo;What are the best keywords for content marketing in 2024?&rdquo;</p>
            </div>
            <div className="bg-white rounded-lg p-4 border cursor-pointer hover:shadow-md transition-shadow">
              <h3 className="font-medium text-gray-900 mb-2">📱 Social Media</h3>
              <p className="text-sm text-gray-600">&ldquo;Create a social media content calendar for a tech startup&rdquo;</p>
            </div>
            <div className="bg-white rounded-lg p-4 border cursor-pointer hover:shadow-md transition-shadow">
              <h3 className="font-medium text-gray-900 mb-2">📊 Analytics</h3>
              <p className="text-sm text-gray-600">&ldquo;How do I measure the ROI of my content marketing efforts?&rdquo;</p>
            </div>
          </div>
        </div>
      </div>
    </Layout>
  );
}
