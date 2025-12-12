//
//  SettingsView.swift
//  MenzaApp
//
//  User settings and preferences
//

import SwiftUI

struct SettingsView: View {
    @EnvironmentObject var authService: AuthService
    @EnvironmentObject var themeManager: ThemeManager
    @State private var showingLogoutAlert = false
    
    var body: some View {
        NavigationStack {
            List {
                // Profile Section
                Section {
                    NavigationLink(destination: ProfileEditView()) {
                        HStack(spacing: 14) {
                            Circle()
                                .fill(
                                    LinearGradient(
                                        colors: [.menzaPurple, .menzaPurpleLight],
                                        startPoint: .topLeading,
                                        endPoint: .bottomTrailing
                                    )
                                )
                                .frame(width: 60, height: 60)
                                .overlay(
                                    Text(String((authService.currentUser?.username ?? "U").prefix(1)).uppercased())
                                        .font(.title2)
                                        .fontWeight(.bold)
                                        .foregroundColor(Color.white)
                                )
                            
                            VStack(alignment: .leading, spacing: 4) {
                                Text(authService.currentUser?.displayName ?? authService.currentUser?.username ?? "User")
                                    .font(.headline)
                                
                                Text("@\(authService.currentUser?.username ?? "username")")
                                    .font(.subheadline)
                                    .foregroundColor(.secondary)
                            }
                            
                            Spacer()
                            
                            if authService.currentUser?.isPremium == true {
                                Image(systemName: "star.fill")
                                    .foregroundColor(.yellow)
                            }
                        }
                        .padding(.vertical, 8)
                    }
                }
                
                // Appearance
                Section("Appearance") {
                    Toggle(isOn: $themeManager.isDarkMode) {
                        Label("Dark Mode", systemImage: "moon.fill")
                    }
                    .tint(.menzaPurple)
                }
                
                // Privacy & Security
                Section("Privacy & Security") {
                    NavigationLink {
                        PrivacySettingsView()
                    } label: {
                        Label("Privacy", systemImage: "hand.raised.fill")
                    }
                    
                    NavigationLink {
                        SecuritySettingsView()
                    } label: {
                        Label("Security", systemImage: "lock.shield.fill")
                    }
                    
                    NavigationLink {
                        BlockedUsersView()
                    } label: {
                        Label("Blocked Users", systemImage: "nosign")
                    }
                }
                
                // Notifications
                Section("Notifications") {
                    NavigationLink {
                        NotificationSettingsView()
                    } label: {
                        Label("Push Notifications", systemImage: "bell.fill")
                    }
                }
                
                // Premium
                Section {
                    NavigationLink {
                        PremiumView()
                    } label: {
                        HStack {
                            Label("Menza Premium", systemImage: "star.circle.fill")
                                .foregroundColor(.yellow)
                            
                            Spacer()
                            
                            if authService.currentUser?.isPremium != true {
                                Text("Upgrade")
                                    .font(.caption)
                                    .foregroundColor(Color.white)
                                    .padding(.horizontal, 10)
                                    .padding(.vertical, 4)
                                    .background(Color.menzaPurple)
                                    .cornerRadius(12)
                            }
                        }
                    }
                }
                
                // Help & Support
                Section("Help & Support") {
                    Link(destination: URL(string: "https://menza.onrender.com/app/privacy")!) {
                        Label("Privacy Policy", systemImage: "doc.text.fill")
                    }
                    
                    Link(destination: URL(string: "https://menza.onrender.com/terms")!) {
                        Label("Terms of Service", systemImage: "doc.plaintext.fill")
                    }
                    
                    NavigationLink {
                        AboutView()
                    } label: {
                        Label("About Menza", systemImage: "info.circle.fill")
                    }
                }
                
                // Account Actions
                Section {
                    Button(role: .destructive) {
                        showingLogoutAlert = true
                    } label: {
                        Label("Sign Out", systemImage: "rectangle.portrait.and.arrow.right")
                    }
                }
            }
            .navigationTitle("Settings")
            .alert("Sign Out", isPresented: $showingLogoutAlert) {
                Button("Cancel", role: .cancel) { }
                Button("Sign Out", role: .destructive) {
                    Task {
                        await authService.logout()
                    }
                }
            } message: {
                Text("Are you sure you want to sign out?")
            }
        }
    }
}

// MARK: - Profile Edit View
struct ProfileEditView: View {
    @EnvironmentObject var authService: AuthService
    @State private var displayName = ""
    @State private var bio = ""
    
    var body: some View {
        Form {
            Section("Profile Picture") {
                HStack {
                    Spacer()
                    Circle()
                        .fill(Color.menzaPurple)
                        .frame(width: 100, height: 100)
                        .overlay(
                            Image(systemName: "camera.fill")
                                .foregroundColor(Color.white)
                        )
                    Spacer()
                }
                .padding(.vertical)
            }
            
            Section("Info") {
                ZStack(alignment: .leading) {
                    if displayName.isEmpty {
                        Text("Display Name")
                            .foregroundColor(Color.gray)
                    }
                    TextField("", text: $displayName)
                }
                
                ZStack(alignment: .topLeading) {
                    if bio.isEmpty {
                        Text("Bio")
                            .foregroundColor(Color.gray)
                            .padding(.top, 8)
                    }
                    TextField("", text: $bio, axis: .vertical)
                        .lineLimit(3...5)
                }
            }
        }
        .navigationTitle("Edit Profile")
        .navigationBarTitleDisplayMode(.inline)
        .toolbar {
            ToolbarItem(placement: .navigationBarTrailing) {
                Button("Save") {
                    // Save changes
                }
            }
        }
        .onAppear {
            displayName = authService.currentUser?.displayName ?? ""
            bio = authService.currentUser?.bio ?? ""
        }
    }
}

// MARK: - Placeholder Views
struct PrivacySettingsView: View {
    var body: some View {
        List {
            Section("Who can see my info") {
                Picker("Last Seen", selection: .constant(0)) {
                    Text("Everyone").tag(0)
                    Text("Contacts").tag(1)
                    Text("Nobody").tag(2)
                }
                
                Picker("Profile Photo", selection: .constant(0)) {
                    Text("Everyone").tag(0)
                    Text("Contacts").tag(1)
                    Text("Nobody").tag(2)
                }
            }
        }
        .navigationTitle("Privacy")
    }
}

struct SecuritySettingsView: View {
    @State private var biometricEnabled = false
    
    var body: some View {
        List {
            Section("App Lock") {
                Toggle("Face ID / Touch ID", isOn: $biometricEnabled)
            }
            
            Section("Password") {
                NavigationLink("Change Password") {
                    Text("Change Password View")
                }
            }
        }
        .navigationTitle("Security")
    }
}

struct BlockedUsersView: View {
    var body: some View {
        List {
            Text("No blocked users")
                .foregroundColor(.secondary)
        }
        .navigationTitle("Blocked Users")
    }
}

struct NotificationSettingsView: View {
    @State private var messagesEnabled = true
    @State private var groupsEnabled = true
    @State private var channelsEnabled = true
    
    var body: some View {
        List {
            Section {
                Toggle("Messages", isOn: $messagesEnabled)
                Toggle("Groups", isOn: $groupsEnabled)
                Toggle("Channels", isOn: $channelsEnabled)
            }
        }
        .navigationTitle("Notifications")
    }
}

struct PremiumView: View {
    var body: some View {
        ScrollView {
            VStack(spacing: 24) {
                Image(systemName: "star.circle.fill")
                    .font(.system(size: 80))
                    .foregroundColor(.yellow)
                
                Text("Menza Premium")
                    .font(.title)
                    .fontWeight(.bold)
                
                VStack(alignment: .leading, spacing: 16) {
                    FeatureRow(icon: "paintbrush.fill", title: "Custom Themes", description: "Personalize your chat appearance")
                    FeatureRow(icon: "face.smiling.fill", title: "Animated Emojis", description: "Express yourself with animations")
                    FeatureRow(icon: "textformat", title: "Premium Fonts", description: "Stand out with unique typography")
                    FeatureRow(icon: "photo.stack.fill", title: "Sticker Packs", description: "Exclusive sticker collections")
                }
                .padding()
                
                Button {
                    // Purchase
                } label: {
                    Text("Subscribe - $4.99/month")
                        .fontWeight(.semibold)
                        .frame(maxWidth: .infinity)
                        .padding()
                        .background(Color.menzaPurple)
                        .foregroundColor(Color.white)
                        .cornerRadius(16)
                }
                .padding(.horizontal)
            }
            .padding(.top, 40)
        }
        .navigationTitle("Premium")
    }
}

struct FeatureRow: View {
    let icon: String
    let title: String
    let description: String
    
    var body: some View {
        HStack(spacing: 14) {
            Image(systemName: icon)
                .font(.title2)
                .foregroundColor(.menzaPurple)
                .frame(width: 30)
            
            VStack(alignment: .leading) {
                Text(title)
                    .fontWeight(.medium)
                Text(description)
                    .font(.caption)
                    .foregroundColor(.secondary)
            }
        }
    }
}

struct AboutView: View {
    var body: some View {
        List {
            Section {
                HStack {
                    Text("Version")
                    Spacer()
                    Text("1.0.0")
                        .foregroundColor(.secondary)
                }
                
                HStack {
                    Text("Build")
                    Spacer()
                    Text("1")
                        .foregroundColor(.secondary)
                }
            }
            
            Section {
                Text("Menza is an end-to-end encrypted messaging platform. Your messages are private and secure.")
                    .font(.subheadline)
                    .foregroundColor(.secondary)
            }
        }
        .navigationTitle("About")
    }
}

// MARK: - Preview
struct SettingsView_Previews: PreviewProvider {
    static var previews: some View {
        SettingsView()
            .environmentObject(AuthService())
            .environmentObject(ThemeManager())
    }
}
