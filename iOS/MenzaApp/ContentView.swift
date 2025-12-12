//
//  ContentView.swift
//  MenzaApp
//
//  Root view that handles navigation based on auth state
//

import SwiftUI

struct ContentView: View {
    @EnvironmentObject var authService: AuthService
    
    var body: some View {
        Group {
            if authService.isAuthenticated {
                MainTabView()
            } else {
                AuthView()
            }
        }
        .animation(.easeInOut, value: authService.isAuthenticated)
    }
}

// MARK: - Main Tab View (After Login)
struct MainTabView: View {
    @State private var selectedTab = 0
    
    var body: some View {
        TabView(selection: $selectedTab) {
            ChatsListView()
                .tabItem {
                    Image(systemName: "message.fill")
                    Text("Chats")
                }
                .tag(0)
            
            ChannelsView()
                .tabItem {
                    Image(systemName: "megaphone.fill")
                    Text("Channels")
                }
                .tag(1)
            
            BotsView()
                .tabItem {
                    Image(systemName: "cpu.fill")
                    Text("Bots")
                }
                .tag(2)
            
            SettingsView()
                .tabItem {
                    Image(systemName: "gearshape.fill")
                    Text("Settings")
                }
                .tag(3)
        }
        .tint(Color.menzaPurple)
    }
}

// MARK: - Preview
struct ContentView_Previews: PreviewProvider {
    static var previews: some View {
        let authService = AuthService()
        let themeManager = ThemeManager()
        
        return ContentView()
            .environmentObject(authService)
            .environmentObject(themeManager)
    }
}
