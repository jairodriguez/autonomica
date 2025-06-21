'use client';

import { SignIn } from '@clerk/nextjs';

export default function SignInPage() {
  return (
    <div className="min-h-screen bg-gray-900 flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-white mb-2">Welcome back</h1>
          <p className="text-gray-400">Sign in to access your AI agent management dashboard</p>
        </div>

        {/* Clerk Sign In Component with Dark Theme */}
        <div className="bg-gray-800 rounded-lg border border-gray-700 p-6">
          <SignIn 
            appearance={{
              elements: {
                rootBox: "w-full",
                card: "bg-transparent shadow-none border-0 p-0",
                headerTitle: "text-gray-100 text-xl font-semibold",
                headerSubtitle: "text-gray-400",
                socialButtonsBlockButton: "bg-gray-700 border-gray-600 text-gray-100 hover:bg-gray-600",
                socialButtonsBlockButtonText: "text-gray-100",
                formButtonPrimary: "bg-purple-600 hover:bg-purple-700 border-0 text-white",
                formFieldInput: "bg-gray-700 border-gray-600 text-gray-100 focus:border-purple-500 focus:ring-purple-500",
                formFieldLabel: "text-gray-300",
                identityPreviewText: "text-gray-100",
                identityPreviewEditButton: "text-purple-400 hover:text-purple-300",
                formFieldHintText: "text-gray-400",
                formFieldErrorText: "text-red-400",
                footerActionText: "text-gray-400",
                footerActionLink: "text-purple-400 hover:text-purple-300",
                dividerLine: "bg-gray-600",
                dividerText: "text-gray-400",
                formFieldSuccessText: "text-green-400",
                alertText: "text-gray-100",
                formHeaderTitle: "text-gray-100",
                formHeaderSubtitle: "text-gray-400",
                formResendCodeLink: "text-purple-400 hover:text-purple-300",
                otpCodeFieldInput: "bg-gray-700 border-gray-600 text-gray-100",
                formFieldInputShowPasswordButton: "text-gray-400 hover:text-gray-300"
              },
              layout: {
                socialButtonsPlacement: "top",
                showOptionalFields: false
              }
            }}
          />
        </div>

        {/* Footer */}
        <div className="mt-6 text-center">
          <p className="text-gray-500 text-sm">
            New to Autonomica?{' '}
            <a href="/sign-up" className="text-purple-400 hover:text-purple-300">
              Create an account
            </a>
          </p>
        </div>
      </div>
    </div>
  );
} 