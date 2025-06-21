# 🔐 Clerk Authentication Setup Guide

This guide will help you configure Clerk authentication for the Autonomica frontend.

## 1. Create a Clerk Account

1. Go to [https://clerk.com](https://clerk.com)
2. Sign up for a free account
3. Create a new application
4. Choose "Next.js" as your framework

## 2. Get Your API Keys

In your Clerk dashboard:

1. Navigate to **API Keys** in the sidebar
2. Copy your **Publishable Key** (starts with `pk_`)
3. Copy your **Secret Key** (starts with `sk_`)

## 3. Configure Environment Variables

1. Copy the example environment file:
   ```bash
   cp .env.example .env.local
   ```

2. Edit `.env.local` and add your Clerk keys:
   ```env
   # Replace with your actual Clerk keys
   NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_test_your_actual_publishable_key_here
   CLERK_SECRET_KEY=sk_test_your_actual_secret_key_here
   ```

## 4. Configure Clerk Dashboard

In your Clerk dashboard, configure the following settings:

### Sign-in & Sign-up URLs
- **Sign-in URL**: `http://localhost:3000/sign-in`
- **Sign-up URL**: `http://localhost:3000/sign-up`
- **After sign-in URL**: `http://localhost:3000/projects`
- **After sign-up URL**: `http://localhost:3000/projects`

### Social Login (Optional)
Enable any social providers you want (Google, GitHub, etc.) in the **Social Connections** section.

### User Profile Settings
Configure what user information you want to collect during sign-up in the **User & Authentication** section.

## 5. Test the Authentication

1. Start the development server:
   ```bash
   npm run dev
   ```

2. Visit `http://localhost:3000`
3. Click "Sign In" to test the authentication flow
4. Try creating a new account
5. Verify you can access the `/projects` page after signing in

## 6. Authentication Features Included

✅ **Dark Theme Integration**: All auth components match your ChatGPT-like interface  
✅ **Route Protection**: `/projects` route is protected by middleware  
✅ **Catch-all Routes**: Proper `/sign-in/[[...rest]]` and `/sign-up/[[...rest]]` structure  
✅ **Custom Sign-in/Sign-up Pages**: Beautiful dark-themed auth pages  
✅ **User Button**: Shows user info and provides sign-out functionality  
✅ **Loading States**: Smooth loading experiences during auth checks  
✅ **Responsive Design**: Works on desktop and mobile  

## 7. Troubleshooting

### "Invalid publishable key" error
- Make sure you copied the key correctly from Clerk dashboard
- Verify the key starts with `pk_test_` or `pk_live_`
- Check that you restarted the dev server after adding environment variables

### Authentication not working
- Verify all URLs in Clerk dashboard match your local setup
- Check browser console for any JavaScript errors
- Make sure `.env.local` file is in the project root

### Styling issues
- The dark theme is pre-configured to match your interface
- All Clerk components use custom CSS classes for consistency

### "SignIn/SignUp component not configured correctly" error
- This error occurs if routes aren't set up as catch-all routes
- The solution: Use `/sign-in/[[...rest]]/page.tsx` and `/sign-up/[[...rest]]/page.tsx`
- Ensure middleware doesn't protect these routes (already configured)

## 8. Production Deployment

When deploying to production:

1. Create a new Clerk application for production (or use the same one)
2. Update environment variables with production URLs
3. Configure production URLs in Clerk dashboard
4. Use production API keys (`pk_live_` and `sk_live_`)

## 9. Next Steps

Once authentication is working:
- Users can securely access the project management interface
- User data will be available throughout the app via Clerk's `useUser()` hook
- Ready for backend API integration with Clerk token validation

---

**Need help?** Check the [Clerk Documentation](https://clerk.com/docs) or the `autonomica-frontend/src/components/auth/` folder for implementation details. 