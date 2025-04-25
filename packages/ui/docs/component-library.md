# Orchestra Component Library Documentation

This document provides detailed information about the Orchestra component library, including how to use components in React and Android applications. The components are designed based on the Figma component mappings and follow a consistent design system.

## Table of Contents

1. [Design System Overview](#design-system-overview)
2. [Color Variables](#color-variables)
3. [Typography](#typography)
4. [Components](#components)
   - [Button](#button)
   - [Card](#card)
   - [Input](#input)
   - [SidebarItem](#sidebaritem)
   - [TopBar](#topbar)
5. [Theme Customization](#theme-customization)
6. [Implementation Guides](#implementation-guides)
   - [React Implementation](#react-implementation)
   - [Android Implementation](#android-implementation)

## Design System Overview

The Orchestra component library implements a dark, tech-focused design system that follows the "tech command center" aesthetic. The design system is built around a set of semantic color variables, consistent typography, and carefully designed components that share a common visual language.

Components are designed to be:
- **Themeable**: Components can adapt to different personas through theme variables
- **Accessible**: Components follow accessibility best practices
- **Consistent**: Components share a common visual language and behavior
- **Flexible**: Components can be customized to fit different use cases

## Color Variables

The component library uses a set of semantic color variables defined in Figma as "Orchestra-Color-Semantic" variables. These variables are used across all components to ensure consistency.

### React Usage

In React, colors are defined in `tokens/variables.js` and can be imported into components:

```jsx
import { colors } from '../tokens/variables';

// Usage
const StyledComponent = styled.div`
  color: ${colors.textPrimary};
  background-color: ${colors.surface};
`;
```

### Android Usage

In Android, colors are defined in `res/values/colors.xml` and can be referenced in layouts and styles:

```xml
<!-- In a layout file -->
<TextView
    android:textColor="@color/text_primary"
    android:background="@color/surface" />
```

## Typography

The design system uses the Inter font family with various weights and sizes to create a clear typographic hierarchy.

### React Usage

Typography styles are defined in `tokens/variables.js` and can be imported:

```jsx
import { typography } from '../tokens/variables';

// Usage
const Heading = styled.h1`
  font-family: ${typography.fontFamily};
  font-size: ${typography.xl};
  font-weight: ${typography.semibold};
`;
```

### Android Usage

Typography styles are defined as text appearances in `res/values/styles.xml`:

```xml
<!-- In a layout file -->
<TextView
    android:textAppearance="@style/Orchestra.Card.Title" />
```

## Components

### Button

Buttons allow users to take actions and make choices with a single tap. Follows the Figma "Button (Primary)" mapping.

#### Variants

- **Primary**: Used for primary actions, styled with accent-primary color
- **Secondary**: Used for secondary actions
- **Outline**: Button with an outline but no background
- **Ghost**: Transparent button with no background or border

#### React Usage

```jsx
import Button, { ButtonVariants, ButtonSizes } from '../components/Button';

// Primary button (default)
<Button onClick={handleClick}>Primary Button</Button>

// Secondary button
<Button variant={ButtonVariants.SECONDARY}>Secondary Button</Button>

// With icon
<Button icon={<IconComponent />}>Button with Icon</Button>

// Size variants
<Button size={ButtonSizes.SMALL}>Small Button</Button>
<Button size={ButtonSizes.MEDIUM}>Medium Button</Button>
<Button size={ButtonSizes.LARGE}>Large Button</Button>

// Disabled state
<Button disabled>Disabled Button</Button>

// Full width
<Button fullWidth>Full Width Button</Button>
```

#### Android Usage

```xml
<!-- Primary button -->
<Button
    style="@style/Orchestra.Button.Primary"
    android:text="Primary Button" />

<!-- Secondary button -->
<Button
    style="@style/Orchestra.Button.Secondary"
    android:text="Secondary Button" />

<!-- Outline button -->
<Button
    style="@style/Orchestra.Button.Outline"
    android:text="Outline Button" />

<!-- Ghost button -->
<Button
    style="@style/Orchestra.Button.Ghost"
    android:text="Ghost Button" />
```

### Card

Cards contain content and actions about a single subject. Follows the Figma "Card (Default)" mapping.

#### Variants

- **Default**: Standard card with subtle border
- **Elevated**: Card with shadow elevation

#### React Usage

```jsx
import Card from '../components/Card';

// Basic card
<Card>
  <p>Card content goes here</p>
</Card>

// Card with title and content
<Card title="Card Title">
  <p>Card content goes here</p>
</Card>

// Card with title, subtitle, and content
<Card 
  title="Card Title" 
  subtitle="Card subtitle"
  headerDivider={true}
>
  <p>Card content goes here</p>
</Card>

// Card with header, content, and footer
<Card
  title="Card Title"
  footer={<Button>Action</Button>}
  footerDivider={true}
  footerAlignEnd={true}
>
  <p>Card content goes here</p>
</Card>

// Elevated, interactive card
<Card
  elevated={true}
  interactive={true}
  onClick={handleCardClick}
>
  <p>Click this card</p>
</Card>
```

#### Android Usage

```xml
<!-- Default card -->
<com.google.android.material.card.MaterialCardView
    style="@style/Orchestra.Card"
    android:layout_width="match_parent"
    android:layout_height="wrap_content">

    <LinearLayout
        android:orientation="vertical"
        android:layout_width="match_parent"
        android:layout_height="wrap_content"
        android:padding="16dp">

        <TextView
            style="@style/Orchestra.Card.Title"
            android:layout_width="match_parent"
            android:layout_height="wrap_content"
            android:text="Card Title" />

        <TextView
            style="@style/Orchestra.Card.Body"
            android:layout_width="match_parent"
            android:layout_height="wrap_content"
            android:layout_marginTop="8dp"
            android:text="Card content goes here" />
    </LinearLayout>
</com.google.android.material.card.MaterialCardView>

<!-- Elevated card -->
<com.google.android.material.card.MaterialCardView
    style="@style/Orchestra.Card.Elevated"
    android:layout_width="match_parent"
    android:layout_height="wrap_content">
    <!-- Content here -->
</com.google.android.material.card.MaterialCardView>
```

### Input

Input components allow users to enter text. Follows the Figma "Input (Default)" mapping.

#### Variants

- **Text Input**: Standard text input
- **Multiline**: Textarea for multi-line content

#### React Usage

```jsx
import Input from '../components/Input';

// Basic text input
<Input 
  label="Username" 
  placeholder="Enter your username"
  onChange={handleChange}
/>

// Required input
<Input 
  label="Email Address" 
  type="email"
  required={true} 
  placeholder="Enter your email"
/>

// With helper text
<Input 
  label="Password" 
  type="password"
  helperText="Password must be at least 8 characters"
/>

// With error
<Input 
  label="Username" 
  value={username}
  error={usernameError ? "Username is already taken" : undefined}
/>

// Multiline textarea
<Input 
  label="Message" 
  multiline={true}
  rows={4}
/>

// Disabled state
<Input 
  label="Username" 
  disabled={true}
  value="johndoe"
/>
```

#### Android Usage

```xml
<!-- Basic text input -->
<com.google.android.material.textfield.TextInputLayout
    style="@style/Orchestra.TextInputLayout"
    android:layout_width="match_parent"
    android:layout_height="wrap_content"
    android:hint="Username">

    <com.google.android.material.textfield.TextInputEditText
        style="@style/Orchestra.TextInputEditText"
        android:layout_width="match_parent"
        android:layout_height="wrap_content" />
</com.google.android.material.textfield.TextInputLayout>

<!-- Required input with error -->
<com.google.android.material.textfield.TextInputLayout
    style="@style/Orchestra.TextInputLayout"
    android:layout_width="match_parent"
    android:layout_height="wrap_content"
    android:hint="Email Address"
    app:errorEnabled="true"
    app:errorText="Please enter a valid email address">

    <com.google.android.material.textfield.TextInputEditText
        style="@style/Orchestra.TextInputEditText"
        android:layout_width="match_parent"
        android:layout_height="wrap_content"
        android:inputType="textEmailAddress" />
</com.google.android.material.textfield.TextInputLayout>
```

### SidebarItem

SidebarItem components are used for navigation in a sidebar. Follows the Figma "Sidebar Item" mapping.

#### Variants

- **Default**: Standard sidebar item
- **Active**: Currently selected sidebar item

#### React Usage

```jsx
import SidebarItem from '../components/SidebarItem';
import { HomeIcon, SettingsIcon } from '../icons';

// Basic sidebar item
<SidebarItem 
  label="Dashboard"
  icon={<HomeIcon />} 
  onClick={handleNavigate}
/>

// Active sidebar item
<SidebarItem
  label="Settings"
  icon={<SettingsIcon />}
  active={true}
/>

// With notification badge
<SidebarItem
  label="Messages"
  icon={<MessageIcon />}
  badge="3"
  badgeVariant="primary"
/>
```

#### Android Usage

```xml
<!-- In a RecyclerView adapter layout -->
<androidx.constraintlayout.widget.ConstraintLayout
    android:layout_width="match_parent"
    android:layout_height="wrap_content"
    android:padding="8dp"
    android:background="@drawable/sidebar_item_background">

    <ImageView
        android:id="@+id/sidebar_icon"
        android:layout_width="20dp"
        android:layout_height="20dp"
        android:tint="@color/text_tertiary"
        app:layout_constraintStart_toStartOf="parent"
        app:layout_constraintTop_toTopOf="parent"
        app:layout_constraintBottom_toBottomOf="parent" />

    <TextView
        android:id="@+id/sidebar_label"
        android:layout_width="0dp"
        android:layout_height="wrap_content"
        android:layout_marginStart="12dp"
        android:textColor="@color/text_secondary"
        android:textSize="16sp"
        app:layout_constraintStart_toEndOf="@id/sidebar_icon"
        app:layout_constraintEnd_toEndOf="parent"
        app:layout_constraintTop_toTopOf="parent"
        app:layout_constraintBottom_toBottomOf="parent" />

    <!-- Badge would be added conditionally -->
</androidx.constraintlayout.widget.ConstraintLayout>
```

### TopBar

The TopBar component provides a consistent navigation header. Follows the Figma "Top Bar Container" mapping.

#### Variants

- **Default**: Standard top bar with title
- **With Subtitle**: Top bar with title and subtitle
- **With Logo**: Top bar with logo and title
- **With Actions**: Top bar with action icons

#### React Usage

```jsx
import TopBar from '../components/TopBar';
import { BellIcon, SearchIcon } from '../icons';

// Basic top bar with title
<TopBar title="Dashboard" />

// With subtitle
<TopBar 
  title="Settings" 
  subtitle="User preferences"
/>

// With logo
<TopBar 
  logo={<img src="/logo.svg" alt="Logo" />}
  title="Orchestra"
/>

// With action icons
<TopBar
  title="Dashboard"
  actionIcons={[<SearchIcon />, <BellIcon />]}
/>

// With avatar
<TopBar
  title="Profile"
  avatarSrc="/avatar.jpg"
  onAvatarClick={handleProfileClick}
/>

// With custom center content (e.g., search bar)
<TopBar
  title="Search"
  centerContent={<SearchInput placeholder="Search..." />}
/>
```

#### Android Usage

```xml
<!-- In layout file -->
<androidx.appcompat.widget.Toolbar
    android:id="@+id/toolbar"
    style="@style/Orchestra.TopBar"
    android:layout_width="match_parent"
    android:layout_height="wrap_content"
    app:title="Dashboard"
    app:titleTextAppearance="@style/Orchestra.TopBar.Title" />
```

## Theme Customization

The component library supports theme customization to match different personas or brands.

### React Theme Customization

```jsx
import { ThemeProvider } from 'styled-components';
import { themes } from '../tokens/variables';

// Create a custom theme
const customTheme = {
  colors: {
    ...themes.neutral,  // Base theme
    accentPrimary: '#FF5722',  // Override accent color
  }
};

// Apply theme
<ThemeProvider theme={customTheme}>
  <App />
</ThemeProvider>
```

### Android Theme Customization

```xml
<!-- In styles.xml -->
<style name="Orchestra.Theme.Custom" parent="Orchestra.Base">
    <item name="colorPrimary">#FF5722</item>
    <item name="colorPrimaryVariant">#E64A19</item>
</style>

<!-- In AndroidManifest.xml -->
<application
    android:theme="@style/Orchestra.Theme.Custom">
    <!-- ... -->
</application>
```

## Implementation Guides

### React Implementation

1. **Install dependencies:**
   ```bash
   npm install styled-components
   ```

2. **Import and use components:**
   ```jsx
   import Button from 'packages/ui/src/components/Button';
   import Card from 'packages/ui/src/components/Card';
   import Input from 'packages/ui/src/components/Input';
   
   function MyComponent() {
     return (
       <Card title="Login Form">
         <Input label="Username" />
         <Input label="Password" type="password" />
         <Button>Log In</Button>
       </Card>
     );
   }
   ```

3. **Initialize theme:**
   ```jsx
   import { ThemeProvider } from 'styled-components';
   import { themes } from 'packages/ui/src/tokens/variables';
   
   function App() {
     return (
       <ThemeProvider theme={themes.neutral}>
         <AppContent />
       </ThemeProvider>
     );
   }
   ```

### Android Implementation

1. **Add dependencies to your app's build.gradle:**
   ```gradle
   dependencies {
       implementation 'com.google.android.material:material:1.6.0'
       // Other dependencies
   }
   ```

2. **Set application theme in AndroidManifest.xml:**
   ```xml
   <application
       android:theme="@style/Orchestra.Theme.Neutral">
       <!-- Application components -->
   </application>
   ```

3. **Use components in layout files:**
   ```xml
   <LinearLayout
       android:layout_width="match_parent"
       android:layout_height="match_parent"
       android:orientation="vertical"
       android:background="@color/background">
       
       <androidx.appcompat.widget.Toolbar
           style="@style/Orchestra.TopBar"
           android:layout_width="match_parent"
           android:layout_height="wrap_content"
           app:title="Login" />
           
       <com.google.android.material.card.MaterialCardView
           style="@style/Orchestra.Card"
           android:layout_width="match_parent"
           android:layout_height="wrap_content"
           android:layout_margin="16dp">
           
           <!-- Input fields and button -->
           
       </com.google.android.material.card.MaterialCardView>
   </LinearLayout>
   ```

---

This documentation provides a comprehensive overview of the Orchestra component library. For specific implementation details, refer to the individual component files in the repository.
