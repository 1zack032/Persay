//
//  AuthService.swift
//  MenzaApp
//
//  Authentication service
//

import Foundation
import SwiftUI

@MainActor
class AuthService: ObservableObject {
    @Published var isAuthenticated = false
    @Published var currentUser: User?
    @Published var isLoading = false
    @Published var error: String?
    
    private let api = APIService.shared
    
    init() {
        // Check if user is already logged in
        checkAuthStatus()
    }
    
    // MARK: - Check Auth Status
    func checkAuthStatus() {
        if let savedUsername = UserDefaults.standard.string(forKey: "username"), !savedUsername.isEmpty {
            // Try to validate session with server
            Task {
                do {
                    let response: AuthResponse = try await api.request(
                        endpoint: "/api/auth/status",
                        method: .get,
                        authenticated: true
                    )
                    if response.success, let user = response.user {
                        self.currentUser = user
                        self.isAuthenticated = true
                    } else {
                        clearSession()
                    }
                } catch {
                    // Session might be expired
                    clearSession()
                }
            }
        }
    }
    
    // MARK: - Login
    @discardableResult
    func login(username: String, password: String) async -> Bool {
        isLoading = true
        error = nil
        
        do {
            let request = LoginRequest(username: username, password: password)
            let response: AuthResponse = try await api.request(
                endpoint: "/api/auth/login",
                method: .post,
                body: request,
                authenticated: false
            )
            
            isLoading = false
            
            if response.success {
                if let user = response.user {
                    currentUser = user
                }
                UserDefaults.standard.set(username, forKey: "username")
                isAuthenticated = true
                return true
            } else {
                error = response.message ?? "Login failed"
                return false
            }
        } catch let apiError as APIError {
            isLoading = false
            error = apiError.errorDescription
            return false
        } catch {
            isLoading = false
            self.error = "Network error. Please try again."
            return false
        }
    }
    
    // MARK: - Register
    func register(
        username: String,
        password: String,
        email: String? = nil,
        phone: String? = nil
    ) async -> (success: Bool, seedPhrase: String?) {
        isLoading = true
        error = nil
        
        do {
            let request = RegisterRequest(
                username: username,
                password: password,
                email: email,
                phone: phone
            )
            
            let response: AuthResponse = try await api.request(
                endpoint: "/api/auth/register",
                method: .post,
                body: request,
                authenticated: false
            )
            
            isLoading = false
            
            if response.success {
                // Don't auto-login, show seed phrase first
                return (true, response.seedPhrase)
            } else {
                error = response.message ?? "Registration failed"
                return (false, nil)
            }
        } catch let apiError as APIError {
            isLoading = false
            error = apiError.errorDescription
            return (false, nil)
        } catch {
            isLoading = false
            self.error = "Network error. Please try again."
            return (false, nil)
        }
    }
    
    // MARK: - Logout
    func logout() async {
        do {
            let _: GenericResponse = try await api.request(
                endpoint: "/api/auth/logout",
                method: .post
            )
        } catch {
            // Logout locally even if server fails
        }
        
        clearSession()
    }
    
    // MARK: - Recover Account
    func recoverAccount(username: String, seedPhrase: String, newPassword: String) async -> Bool {
        isLoading = true
        error = nil
        
        struct RecoverRequest: Codable {
            let username: String
            let seed_phrase: String
            let new_password: String
        }
        
        do {
            let request = RecoverRequest(
                username: username,
                seed_phrase: seedPhrase,
                new_password: newPassword
            )
            
            let response: GenericResponse = try await api.request(
                endpoint: "/api/auth/recover",
                method: .post,
                body: request,
                authenticated: false
            )
            
            isLoading = false
            
            if response.success {
                return true
            } else {
                error = response.message ?? "Recovery failed"
                return false
            }
        } catch {
            isLoading = false
            self.error = "Network error. Please try again."
            return false
        }
    }
    
    // MARK: - Clear Session
    private func clearSession() {
        UserDefaults.standard.removeObject(forKey: "username")
        HTTPCookieStorage.shared.cookies?.forEach { HTTPCookieStorage.shared.deleteCookie($0) }
        currentUser = nil
        isAuthenticated = false
    }
}
