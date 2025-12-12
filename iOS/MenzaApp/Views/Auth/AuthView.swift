//
//  AuthView.swift
//  MenzaApp
//
//  Login and Registration views
//

import SwiftUI

struct AuthView: View {
    @EnvironmentObject var themeManager: ThemeManager
    @State private var showingLogin = true
    
    var body: some View {
        NavigationStack {
            ZStack {
                // Background gradient - responds to theme
                Group {
                    if themeManager.isDarkMode {
                        LinearGradient(
                            colors: [Color.menzaBgDark, Color.menzaBgSecondary],
                            startPoint: .top,
                            endPoint: .bottom
                        )
                    } else {
                        LinearGradient(
                            colors: [Color(hex: "f8f7ff"), Color(hex: "ede9fe")],
                            startPoint: .top,
                            endPoint: .bottom
                        )
                    }
                }
                .ignoresSafeArea()
                
                // Animated background orbs
                GeometryReader { geo in
                    Circle()
                        .fill(Color.menzaPurple.opacity(themeManager.isDarkMode ? 0.3 : 0.2))
                        .frame(width: 300, height: 300)
                        .blur(radius: 60)
                        .offset(x: -50, y: -100)
                    
                    Circle()
                        .fill(Color.menzaPink.opacity(themeManager.isDarkMode ? 0.2 : 0.15))
                        .frame(width: 250, height: 250)
                        .blur(radius: 50)
                        .offset(x: geo.size.width - 100, y: geo.size.height - 200)
                }
                
                VStack(spacing: 0) {
                    // Theme Toggle Button - Top Right
                    HStack {
                        Spacer()
                        Button {
                            withAnimation(.easeInOut(duration: 0.3)) {
                                themeManager.toggle()
                            }
                        } label: {
                            Image(systemName: themeManager.isDarkMode ? "sun.max" : "moon")
                                .font(.title2)
                                .fontWeight(.medium)
                                .foregroundColor(themeManager.isDarkMode ? .white.opacity(0.8) : .menzaPurple.opacity(0.8))
                                .padding(12)
                                .background(
                                    Circle()
                                        .fill(themeManager.isDarkMode ? Color.white.opacity(0.15) : Color.menzaPurple.opacity(0.15))
                                        .overlay(
                                            Circle()
                                                .stroke(themeManager.isDarkMode ? Color.white.opacity(0.3) : Color.menzaPurple.opacity(0.3), lineWidth: 1)
                                        )
                                )
                        }
                        .padding(.trailing, 20)
                        .padding(.top, 10)
                    }
                    
                    // Logo
                    VStack(spacing: 8) {
                        Text("MENZA")
                            .font(.system(size: 42, weight: .bold, design: .rounded))
                            .foregroundStyle(
                                LinearGradient(
                                    colors: themeManager.isDarkMode 
                                        ? [Color.white, .menzaPurpleLight, .menzaPurple]
                                        : [.menzaPurple, .menzaPurpleLight, .menzaPink],
                                    startPoint: .leading,
                                    endPoint: .trailing
                                )
                            )
                        
                        Text("Encrypted Messaging")
                            .font(.subheadline)
                            .foregroundColor(Color.gray)
                    }
                    .padding(.top, 20)
                    .padding(.bottom, 40)
                    
                    // Content - Flexible area
                    if showingLogin {
                        LoginView(showingLogin: $showingLogin)
                            .transition(.asymmetric(
                                insertion: .move(edge: .trailing),
                                removal: .move(edge: .leading)
                            ))
                        
                        Spacer()
                        
                        // Footer for Login
                        AuthFooterView()
                    } else {
                        RegisterView(showingLogin: $showingLogin)
                            .transition(.asymmetric(
                                insertion: .move(edge: .trailing),
                                removal: .move(edge: .leading)
                            ))
                    }
                }
            }
        }
        .preferredColorScheme(themeManager.colorScheme)
    }
}

// MARK: - Auth Footer
struct AuthFooterView: View {
    var body: some View {
        VStack(spacing: 4) {
            HStack(spacing: 4) {
                Image(systemName: "lock.shield.fill")
                    .foregroundColor(.menzaPurple)
                Text("End-to-end encrypted")
                    .font(.caption)
                    .foregroundColor(Color.gray)
            }
            
            Text("Your messages are private")
                .font(.caption2)
                .foregroundColor(.gray.opacity(0.7))
        }
        .padding(.bottom, 30)
    }
}

// MARK: - Login View
struct LoginView: View {
    @EnvironmentObject var authService: AuthService
    @EnvironmentObject var themeManager: ThemeManager
    @Binding var showingLogin: Bool
    
    @State private var username = ""
    @State private var password = ""
    @State private var showPassword = false
    @FocusState private var focusedField: Field?
    
    enum Field {
        case username, password
    }
    
    var body: some View {
        VStack(spacing: 20) {
            // Title
            VStack(spacing: 4) {
                Text("Welcome back")
                    .font(.title2)
                    .fontWeight(.bold)
                    .foregroundColor(themeManager.isDarkMode ? Color.white : Color.black)
                
                Text("Sign in to continue")
                    .font(.subheadline)
                    .foregroundColor(Color.gray)
            }
            .padding(.bottom, 10)
            
            // Form
            VStack(spacing: 16) {
                // Username
                MenzaTextField(
                    icon: "person.fill",
                    placeholder: "Username",
                    text: $username
                )
                .focused($focusedField, equals: .username)
                
                // Password
                MenzaSecureField(
                    icon: "lock.fill",
                    placeholder: "Password",
                    text: $password,
                    showPassword: $showPassword
                )
                .focused($focusedField, equals: .password)
            }
            .padding(.horizontal, 24)
            
            // Error message
            if let error = authService.error {
                Text(error)
                    .font(.caption)
                    .foregroundColor(Color.red)
                    .padding(.horizontal)
            }
            
            // Login Button
            Button {
                Task {
                    await authService.login(username: username, password: password)
                }
            } label: {
                HStack {
                    if authService.isLoading {
                        ProgressView()
                            .tint(Color.white)
                    } else {
                        Text("Sign In")
                            .fontWeight(.semibold)
                    }
                }
                .frame(maxWidth: .infinity)
                .padding(.vertical, 16)
                .background(
                    LinearGradient(
                        colors: [.menzaPurple, .menzaPurpleLight],
                        startPoint: .leading,
                        endPoint: .trailing
                    )
                )
                .foregroundColor(Color.white)
                .cornerRadius(16)
            }
            .disabled(username.isEmpty || password.isEmpty || authService.isLoading)
            .opacity(username.isEmpty || password.isEmpty ? 0.6 : 1)
            .padding(.horizontal, 24)
            .padding(.top, 10)
            
            // Forgot password
            NavigationLink {
                RecoverView()
            } label: {
                Text("Forgot password?")
                    .font(.subheadline)
                    .foregroundColor(.menzaPurple)
            }
            .padding(.top, 8)
            
            // Register link
            HStack {
                Text("Don't have an account?")
                    .foregroundColor(Color.gray)
                Button {
                    withAnimation(.spring(response: 0.4)) {
                        showingLogin = false
                    }
                } label: {
                    Text("Create one")
                        .fontWeight(.semibold)
                        .foregroundColor(.menzaPurple)
                }
            }
            .font(.subheadline)
            .padding(.top, 20)
        }
    }
}

// MARK: - Register View
struct RegisterView: View {
    @EnvironmentObject var authService: AuthService
    @EnvironmentObject var themeManager: ThemeManager
    @Binding var showingLogin: Bool
    
    @State private var username = ""
    @State private var password = ""
    @State private var confirmPassword = ""
    @State private var email = ""
    @State private var phone = ""
    @State private var agreedToTerms = false
    @State private var isOver18 = false
    @State private var showingSeedPhrase = false
    @State private var seedPhrase: String?
    @State private var showPassword = false
    @State private var showConfirmPassword = false
    
    var isFormValid: Bool {
        !username.isEmpty &&
        !password.isEmpty &&
        password == confirmPassword &&
        password.count >= 8 &&
        agreedToTerms &&
        isOver18
    }
    
    var body: some View {
        ScrollView {
            VStack(spacing: 20) {
                // Title
                VStack(spacing: 4) {
                    Text("Create Account")
                        .font(.title2)
                        .fontWeight(.bold)
                        .foregroundColor(themeManager.isDarkMode ? Color.white : Color.black)
                    
                    Text("Join Menza today")
                        .font(.subheadline)
                        .foregroundColor(Color.gray)
                }
                .padding(.bottom, 10)
                
                // Form
                VStack(spacing: 16) {
                    MenzaTextField(
                        icon: "person.fill",
                        placeholder: "Username",
                        text: $username
                    )
                    
                    MenzaSecureField(
                        icon: "lock.fill",
                        placeholder: "Password (min 8 chars)",
                        text: $password,
                        showPassword: $showPassword
                    )
                    
                    MenzaSecureField(
                        icon: "lock.fill",
                        placeholder: "Confirm Password",
                        text: $confirmPassword,
                        showPassword: $showConfirmPassword
                    )
                    
                    MenzaTextField(
                        icon: "envelope.fill",
                        placeholder: "Email (optional)",
                        text: $email
                    )
                    
                    MenzaTextField(
                        icon: "phone.fill",
                        placeholder: "Phone (optional)",
                        text: $phone
                    )
                }
                .padding(.horizontal, 24)
                
                // Checkboxes
                VStack(spacing: 12) {
                    Toggle(isOn: $isOver18) {
                        Text("I am 18 years or older")
                            .font(.subheadline)
                            .foregroundColor(themeManager.isDarkMode ? Color.white : Color.black)
                    }
                    .toggleStyle(CheckboxToggleStyle())
                    
                    Toggle(isOn: $agreedToTerms) {
                        Text("I agree to the Terms & Privacy Policy")
                            .font(.subheadline)
                            .foregroundColor(themeManager.isDarkMode ? Color.white : Color.black)
                    }
                    .toggleStyle(CheckboxToggleStyle())
                }
                .padding(.horizontal, 24)
                
                // Password mismatch warning
                if !confirmPassword.isEmpty && password != confirmPassword {
                    Text("Passwords don't match")
                        .font(.caption)
                        .foregroundColor(Color.red)
                }
                
                // Error message
                if let error = authService.error {
                    Text(error)
                        .font(.caption)
                        .foregroundColor(Color.red)
                        .padding(.horizontal)
                }
                
                // Register Button
                Button {
                    Task {
                        let result = await authService.register(
                            username: username,
                            password: password,
                            email: email.isEmpty ? nil : email,
                            phone: phone.isEmpty ? nil : phone
                        )
                        if result.success {
                            seedPhrase = result.seedPhrase
                            showingSeedPhrase = true
                        }
                    }
                } label: {
                    HStack {
                        if authService.isLoading {
                            ProgressView()
                                .tint(Color.white)
                        } else {
                            Text("Create Account")
                                .fontWeight(.semibold)
                        }
                    }
                    .frame(maxWidth: .infinity)
                    .padding(.vertical, 16)
                    .background(
                        LinearGradient(
                            colors: [.menzaPurple, .menzaPurpleLight],
                            startPoint: .leading,
                            endPoint: .trailing
                        )
                    )
                    .foregroundColor(Color.white)
                    .cornerRadius(16)
                    .shadow(color: .menzaPurple.opacity(0.3), radius: 8, x: 0, y: 4)
                }
                .disabled(!isFormValid || authService.isLoading)
                .opacity(isFormValid ? 1 : 0.6)
                .padding(.horizontal, 24)
                .padding(.top, 8)
                
                // Login link
                HStack {
                    Text("Already have an account?")
                        .foregroundColor(Color.gray)
                    Button {
                        withAnimation(.spring(response: 0.4)) {
                            showingLogin = true
                        }
                    } label: {
                        Text("Sign in")
                            .fontWeight(.semibold)
                            .foregroundColor(.menzaPurple)
                    }
                }
                .font(.subheadline)
                .padding(.top, 10)
                
                // Footer inside scroll for Register view
                AuthFooterView()
                    .padding(.top, 20)
            }
            .padding(.bottom, 20)
        }
        .scrollDismissesKeyboard(.interactively)
        .sheet(isPresented: $showingSeedPhrase) {
            SeedPhraseView(seedPhrase: seedPhrase ?? "", onContinue: {
                showingSeedPhrase = false
                showingLogin = true
            })
        }
    }
}

// MARK: - Custom Text Field with Visible Placeholder
struct MenzaTextField: View {
    @EnvironmentObject var themeManager: ThemeManager
    let icon: String
    let placeholder: String
    @Binding var text: String
    
    var body: some View {
        HStack(spacing: 12) {
            Image(systemName: icon)
                .foregroundColor(themeManager.isDarkMode ? .white.opacity(0.6) : .menzaPurple.opacity(0.7))
                .frame(width: 24)
            
            ZStack(alignment: .leading) {
                if text.isEmpty {
                    Text(placeholder)
                        .foregroundColor(themeManager.isDarkMode ? .white.opacity(0.5) : Color.gray)
                }
                TextField("", text: $text)
                    .foregroundColor(themeManager.isDarkMode ? Color.white : Color.black)
                    .autocapitalization(.none)
                    .autocorrectionDisabled()
            }
        }
        .padding()
        .background(themeManager.isDarkMode ? Color.white.opacity(0.12) : Color.white)
        .cornerRadius(16)
        .overlay(
            RoundedRectangle(cornerRadius: 16)
                .stroke(themeManager.isDarkMode ? Color.white.opacity(0.2) : Color.menzaPurple.opacity(0.3), lineWidth: 1)
        )
        .shadow(color: themeManager.isDarkMode ? .clear : .black.opacity(0.05), radius: 5, x: 0, y: 2)
    }
}

// MARK: - Custom Secure Field with Visible Placeholder
struct MenzaSecureField: View {
    @EnvironmentObject var themeManager: ThemeManager
    let icon: String
    let placeholder: String
    @Binding var text: String
    @Binding var showPassword: Bool
    
    var body: some View {
        HStack(spacing: 12) {
            Image(systemName: icon)
                .foregroundColor(themeManager.isDarkMode ? .white.opacity(0.6) : .menzaPurple.opacity(0.7))
                .frame(width: 24)
            
            ZStack(alignment: .leading) {
                if text.isEmpty {
                    Text(placeholder)
                        .foregroundColor(themeManager.isDarkMode ? .white.opacity(0.5) : Color.gray)
                }
                
                if showPassword {
                    TextField("", text: $text)
                        .foregroundColor(themeManager.isDarkMode ? Color.white : Color.black)
                } else {
                    SecureField("", text: $text)
                        .foregroundColor(themeManager.isDarkMode ? Color.white : Color.black)
                }
            }
            
            Button {
                showPassword.toggle()
            } label: {
                Image(systemName: showPassword ? "eye.slash.fill" : "eye.fill")
                    .foregroundColor(themeManager.isDarkMode ? .white.opacity(0.5) : Color.gray)
            }
        }
        .padding()
        .background(themeManager.isDarkMode ? Color.white.opacity(0.12) : Color.white)
        .cornerRadius(16)
        .overlay(
            RoundedRectangle(cornerRadius: 16)
                .stroke(themeManager.isDarkMode ? Color.white.opacity(0.2) : Color.menzaPurple.opacity(0.3), lineWidth: 1)
        )
        .shadow(color: themeManager.isDarkMode ? .clear : .black.opacity(0.05), radius: 5, x: 0, y: 2)
    }
}

struct CheckboxToggleStyle: ToggleStyle {
    func makeBody(configuration: Configuration) -> some View {
        HStack {
            Image(systemName: configuration.isOn ? "checkmark.square.fill" : "square")
                .foregroundColor(configuration.isOn ? .menzaPurple : Color.gray)
                .font(.title3)
                .onTapGesture {
                    configuration.isOn.toggle()
                }
            configuration.label
        }
    }
}

// MARK: - Seed Phrase View
struct SeedPhraseView: View {
    let seedPhrase: String
    let onContinue: () -> Void
    @State private var hasCopied = false
    
    var words: [String] {
        seedPhrase.split(separator: " ").map(String.init)
    }
    
    var body: some View {
        VStack(spacing: 24) {
            // Warning
            VStack(spacing: 12) {
                Image(systemName: "exclamationmark.triangle.fill")
                    .font(.system(size: 50))
                    .foregroundColor(.orange)
                
                Text("Save Your Recovery Phrase")
                    .font(.title2)
                    .fontWeight(.bold)
                
                Text("Write down these 12 words in order. You'll need them to recover your account if you forget your password.")
                    .font(.subheadline)
                    .foregroundColor(.secondary)
                    .multilineTextAlignment(.center)
            }
            .padding(.top, 30)
            
            // Words grid
            LazyVGrid(columns: [
                GridItem(.flexible()),
                GridItem(.flexible()),
                GridItem(.flexible())
            ], spacing: 12) {
                ForEach(Array(words.enumerated()), id: \.offset) { index, word in
                    HStack {
                        Text("\(index + 1).")
                            .font(.caption)
                            .foregroundColor(.secondary)
                            .frame(width: 20)
                        Text(word)
                            .font(.system(.body, design: .monospaced))
                            .fontWeight(.medium)
                    }
                    .padding(.horizontal, 12)
                    .padding(.vertical, 10)
                    .background(Color(.systemGray6))
                    .cornerRadius(10)
                }
            }
            .padding(.horizontal)
            
            // Copy button
            Button {
                UIPasteboard.general.string = seedPhrase
                hasCopied = true
                
                // Haptic
                let generator = UINotificationFeedbackGenerator()
                generator.notificationOccurred(.success)
            } label: {
                HStack {
                    Image(systemName: hasCopied ? "checkmark" : "doc.on.doc")
                    Text(hasCopied ? "Copied!" : "Copy to Clipboard")
                }
                .foregroundColor(.menzaPurple)
            }
            
            Spacer()
            
            // Warning text
            Text("⚠️ Never share your recovery phrase. Anyone with these words can access your account.")
                .font(.caption)
                .foregroundColor(.orange)
                .multilineTextAlignment(.center)
                .padding(.horizontal)
            
            // Continue button
            Button(action: onContinue) {
                Text("I've Saved My Phrase")
                    .fontWeight(.semibold)
                    .frame(maxWidth: .infinity)
                    .padding(.vertical, 16)
                    .background(
                        LinearGradient(
                            colors: [.menzaPurple, .menzaPurpleLight],
                            startPoint: .leading,
                            endPoint: .trailing
                        )
                    )
                    .foregroundColor(Color.white)
                    .cornerRadius(16)
            }
            .padding(.horizontal, 24)
            .padding(.bottom, 30)
        }
    }
}

// MARK: - Recover View
struct RecoverView: View {
    @EnvironmentObject var authService: AuthService
    @Environment(\.dismiss) var dismiss
    
    @State private var username = ""
    @State private var seedPhrase = ""
    @State private var newPassword = ""
    @State private var showSuccess = false
    @State private var showPassword = false
    
    var body: some View {
        ZStack {
            Color.menzaBgDark.ignoresSafeArea()
            
            VStack(spacing: 24) {
                Text("Recover Account")
                    .font(.title2)
                    .fontWeight(.bold)
                    .foregroundColor(Color.white)
                
                VStack(spacing: 16) {
                    MenzaTextField(icon: "person.fill", placeholder: "Username", text: $username)
                    
                    VStack(alignment: .leading, spacing: 8) {
                        Text("Recovery Phrase")
                            .font(.subheadline)
                            .foregroundColor(.white.opacity(0.7))
                        
                        ZStack(alignment: .topLeading) {
                            if seedPhrase.isEmpty {
                                Text("Enter your 12-word phrase")
                                    .foregroundColor(.white.opacity(0.5))
                                    .padding(.top, 8)
                                    .padding(.leading, 4)
                            }
                            TextEditor(text: $seedPhrase)
                                .foregroundColor(Color.white)
                                .scrollContentBackground(.hidden)
                                .frame(height: 100)
                        }
                        .padding(12)
                        .background(Color.white.opacity(0.12))
                        .cornerRadius(12)
                        .overlay(
                            RoundedRectangle(cornerRadius: 12)
                                .stroke(Color.white.opacity(0.2), lineWidth: 1)
                        )
                    }
                    
                    MenzaSecureField(icon: "lock.fill", placeholder: "New Password", text: $newPassword, showPassword: $showPassword)
                }
                .padding(.horizontal, 24)
                
                if let error = authService.error {
                    Text(error)
                        .font(.caption)
                        .foregroundColor(Color.red)
                }
                
                Button {
                    Task {
                        let success = await authService.recoverAccount(
                            username: username,
                            seedPhrase: seedPhrase,
                            newPassword: newPassword
                        )
                        if success {
                            showSuccess = true
                        }
                    }
                } label: {
                    Text("Recover Account")
                        .fontWeight(.semibold)
                        .frame(maxWidth: .infinity)
                        .padding(.vertical, 16)
                        .background(Color.menzaPurple)
                        .foregroundColor(Color.white)
                        .cornerRadius(16)
                }
                .padding(.horizontal, 24)
                
                Spacer()
            }
            .padding(.top, 30)
        }
        .alert("Success!", isPresented: $showSuccess) {
            Button("OK") { dismiss() }
        } message: {
            Text("Your password has been reset. You can now login with your new password.")
        }
    }
}

// MARK: - Preview
struct AuthView_Previews: PreviewProvider {
    static var previews: some View {
        AuthView()
            .environmentObject(AuthService())
            .environmentObject(ThemeManager())
    }
}
