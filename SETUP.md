# 🚀 Orchestra AI - Setup Guide

Welcome to Orchestra AI! This guide will help you get both the web and mobile mockups up and running.

## 📋 Prerequisites

- **Node.js** 16+ 
- **npm** or **yarn**
- **React Native CLI** (for mobile development)
- **Xcode** (for iOS development)
- **Android Studio** (for Android development)

## 🌐 Web Application Setup

### Quick Start (HTML Mockups)
The fastest way to view the web mockups:

```bash
cd web/public
python -m http.server 8000
# or
npx serve .
```

Then open:
- Homepage: http://localhost:8000/index.html
- Dashboard: http://localhost:8000/dashboard.html
- Workflow Builder: http://localhost:8000/../mockups/workflow-builder.html

### Full React Development

1. **Install Dependencies**
   ```bash
   cd web
   npm install
   ```

2. **Start Development Server**
   ```bash
   npm start
   ```

3. **Build for Production**
   ```bash
   npm run build
   ```

4. **Run Tests**
   ```bash
   npm test
   ```

## 📱 Mobile Application Setup

### View Mobile Mockups
Open the HTML mockups in your browser:

```bash
cd mobile/mockups
python -m http.server 8001
```

Then open:
- Home Screen: http://localhost:8001/home-screen.html
- Analytics: http://localhost:8001/analytics-screen.html

### Full React Native Development

1. **Install Dependencies**
   ```bash
   cd mobile
   npm install
   ```

2. **iOS Setup**
   ```bash
   cd ios
   pod install
   cd ..
   npm run ios
   ```

3. **Android Setup**
   ```bash
   npm run android
   ```

4. **Start Metro Bundler**
   ```bash
   npm start
   ```

## 🎨 Design System

### Colors
- **Primary**: Blue gradients (#3b82f6 to #1d4ed8)
- **Success**: Green gradients (#10b981 to #059669)
- **Warning**: Yellow gradients (#f59e0b to #d97706)
- **Danger**: Red gradients (#ef4444 to #dc2626)

### Typography
- **Font Family**: Inter
- **Weights**: 300, 400, 500, 600, 700

### Components
All components are built with:
- **Tailwind CSS** for styling
- **TypeScript** for type safety
- **Responsive design** for all screen sizes
- **Accessibility** features built-in

## 🔧 Development Tools

### Recommended VS Code Extensions
- ES7+ React/Redux/React-Native snippets
- Tailwind CSS IntelliSense
- TypeScript Importer
- Auto Rename Tag
- Prettier - Code formatter

### Linting & Formatting
```bash
# Web
cd web
npm run lint
npm run format

# Mobile
cd mobile
npm run lint
```

## 📁 Project Structure

```
orchestra-dev/
├── web/                    # Web application
│   ├── public/            # Static HTML mockups
│   ├── src/               # React source code
│   ├── mockups/           # Additional mockups
│   └── package.json
├── mobile/                 # Mobile application
│   ├── src/               # React Native source
│   ├── mockups/           # Mobile mockups
│   ├── ios/               # iOS project files
│   ├── android/           # Android project files
│   └── package.json
└── shared/                 # Shared components
    ├── components/        # Reusable UI components
    ├── utils/             # Utility functions
    └── types/             # TypeScript definitions
```

## 🌟 Features Included

### Web Application
- ✅ Modern responsive homepage
- ✅ Feature-rich dashboard
- ✅ Interactive workflow builder
- ✅ Real-time data updates
- ✅ Beautiful animations
- ✅ Accessible design

### Mobile Application
- ✅ Native-feeling interface
- ✅ Touch-optimized interactions
- ✅ Real-time analytics
- ✅ Gesture support
- ✅ Status bar integration
- ✅ Bottom navigation

### Shared Components
- ✅ Button component with variants
- ✅ TypeScript interfaces
- ✅ Consistent styling
- ✅ Reusable utilities

## 🚀 Deployment

### Web Deployment
```bash
# Build for production
cd web
npm run build

# Deploy to Vercel
vercel --prod

# Deploy to Netlify
netlify deploy --prod --dir=build
```

### Mobile Deployment
```bash
# iOS
cd mobile
npm run build:ios

# Android
npm run build:android
```

## 🎯 Next Steps

1. **Customize the Design**: Update colors, fonts, and layouts in the CSS/styles
2. **Add Real Data**: Connect to your backend APIs
3. **Enhance Interactions**: Add more animations and micro-interactions
4. **Test on Devices**: Ensure compatibility across different screen sizes
5. **Performance**: Optimize images and bundle sizes

## 📚 Resources

- [React Documentation](https://reactjs.org/docs)
- [React Native Guide](https://reactnative.dev/docs)
- [Tailwind CSS](https://tailwindcss.com/docs)
- [TypeScript Handbook](https://www.typescriptlang.org/docs)

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

---

**Happy coding! 🎉**

*Built with ❤️ for the future of AI orchestration* 