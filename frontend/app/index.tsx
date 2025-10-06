import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  TextInput,
  ScrollView,
  Image,
  Alert,
  KeyboardAvoidingView,
  Platform,
  StatusBar,
  Modal,
  FlatList,
  ActivityIndicator,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import AsyncStorage from '@react-native-async-storage/async-storage';
import * as ImagePicker from 'expo-image-picker';
import { Ionicons } from '@expo/vector-icons';
import Constants from 'expo-constants';

// Get backend URL from env - FIXED for preview environment
const getBackendUrl = () => {
  if (typeof window !== 'undefined') {
    const hostname = window.location.hostname;
    console.log('🌐 Current hostname:', hostname);
    
    // Preview environment - use relative API path (gets proxied to :8001)
    if (hostname.includes('preview.emergentagent.com') || hostname.includes('smart-closet')) {
      console.log('🔧 PREVIEW MODE: Using relative API path (proxied to backend)');
      return '';  // Use relative path for preview - /api/* gets proxied to :8001
    }
    
    // Production environment - use relative URL  
    if (hostname.includes('emergent.host')) {
      console.log('🚀 PRODUCTION MODE: Using relative API path');
      return '';  // Use relative path for production
    }
  }
  
  // Development/Expo Go fallback
  console.log('💻 DEVELOPMENT MODE: Using localhost backend');
  return 'http://localhost:8001';
};

const BACKEND_URL = getBackendUrl();

// Enhanced onboarding data with visual elements
const GENDER_OPTIONS = [
  { id: 'male', label: 'Male', icon: 'man-outline', color: '#4A90E2' },
  { id: 'female', label: 'Female', icon: 'woman-outline', color: '#F5A623' },
  { id: 'other', label: 'Other', icon: 'people-outline', color: '#7ED321' },
];

const AGE_GROUPS = [
  { id: '12-18', label: '12-18', subtitle: 'Teen Style', icon: 'school-outline', color: '#FF6B6B' },
  { id: '18-25', label: '18-25', subtitle: 'Young Adult', icon: 'rocket-outline', color: '#4ECDC4' },
  { id: '25-30', label: '25-30', subtitle: 'Rising Star', icon: 'trending-up-outline', color: '#45B7D1' },
  { id: '30-40', label: '30-40', subtitle: 'Prime Time', icon: 'star-outline', color: '#96CEB4' },
  { id: '40+', label: '40+', subtitle: 'Established', icon: 'trophy-outline', color: '#FFEAA7' },
];

const PROFESSIONS = [
  { id: 'student', label: 'Student', icon: 'book-outline', color: '#FF7675', bg: '#FFE8E8' },
  { id: 'working', label: 'Working Professional', icon: 'briefcase-outline', color: '#74B9FF', bg: '#E8F4FF' },
  { id: 'entrepreneur', label: 'Entrepreneur', icon: 'bulb-outline', color: '#FDCB6E', bg: '#FFF8E8' },
  { id: 'creative', label: 'Creative', icon: 'color-palette-outline', color: '#E17055', bg: '#FFE8E1' },
  { id: 'athlete', label: 'Athlete', icon: 'fitness-outline', color: '#00B894', bg: '#E8F8F5' },
];

const BODY_SHAPES = {
  female: [
    { id: 'hourglass', label: 'Hourglass', image: 'https://customer-assets.emergentagent.com/job_stylistai/artifacts/53fftmcb_Group%201321316023.png' },
    { id: 'pear', label: 'Pear', image: 'https://customer-assets.emergentagent.com/job_stylistai/artifacts/2w168gmc_Group%201321316024.png' },
    { id: 'apple', label: 'Apple', image: 'https://customer-assets.emergentagent.com/job_stylistai/artifacts/ynwnpelz_Group%201321316025.png' },
    { id: 'rectangle', label: 'Rectangle', image: 'https://customer-assets.emergentagent.com/job_stylistai/artifacts/3yins757_Group%201321316026.png' },
    { id: 'inverted_triangle', label: 'Inverted Triangle', image: 'https://customer-assets.emergentagent.com/job_stylistai/artifacts/c4nyw67g_Group%201321316027.png' },
  ],
  male: [
    { id: 'rectangle', label: 'Rectangle', image: 'https://customer-assets.emergentagent.com/job_stylistai/artifacts/pfdonfcy_Group%201321316029.png' },
    { id: 'triangle', label: 'Triangle', image: 'https://customer-assets.emergentagent.com/job_stylistai/artifacts/qkjzx3dg_Group%201321316028.png' },
    { id: 'oval', label: 'Oval', image: 'https://customer-assets.emergentagent.com/job_stylistai/artifacts/cbdjggb8_Group%201321316030.png' },
    { id: 'trapezoid', label: 'Trapezoid', image: 'https://customer-assets.emergentagent.com/job_stylistai/artifacts/0g1mj6e2_Group%201321316031.png' },
    { id: 'inverted_triangle', label: 'Inverted Triangle', image: 'https://customer-assets.emergentagent.com/job_stylistai/artifacts/cetw5hm4_Group%201321316043.png' },
  ],
  other: [
    { id: 'rectangle', label: 'Rectangle', image: 'https://customer-assets.emergentagent.com/job_stylistai/artifacts/pfdonfcy_Group%201321316029.png' },
    { id: 'triangle', label: 'Triangle', image: 'https://customer-assets.emergentagent.com/job_stylistai/artifacts/qkjzx3dg_Group%201321316028.png' },
    { id: 'oval', label: 'Oval', image: 'https://customer-assets.emergentagent.com/job_stylistai/artifacts/cbdjggb8_Group%201321316030.png' },
  ]
};

const SKIN_TONES = [
  { id: 'very_fair', label: 'Very Fair', color: '#F7E7CE', hex: '#F7E7CE' },
  { id: 'fair', label: 'Fair', color: '#F1C27D', hex: '#F1C27D' },
  { id: 'light', label: 'Light', color: '#E0AC69', hex: '#E0AC69' },
  { id: 'medium_light', label: 'Medium Light', color: '#C68642', hex: '#C68642' },
  { id: 'medium', label: 'Medium', color: '#A0522D', hex: '#A0522D' },
  { id: 'medium_deep', label: 'Medium Deep', color: '#8B4513', hex: '#8B4513' },
  { id: 'deep', label: 'Deep', color: '#654321', hex: '#654321' },
  { id: 'very_deep', label: 'Very Deep', color: '#3C1810', hex: '#3C1810' },
];

const PERSONALITY_TYPES = [
  { id: 'bold', label: 'Bold', icon: 'flash-outline', color: '#FF6B6B', description: 'Make a statement' },
  { id: 'minimalist', label: 'Minimalist', icon: 'remove-outline', color: '#95A5A6', description: 'Less is more' },
  { id: 'playful', label: 'Playful', icon: 'happy-outline', color: '#F39C12', description: 'Fun & vibrant' },
  { id: 'classic', label: 'Classic', icon: 'diamond-outline', color: '#2C3E50', description: 'Timeless elegance' },
  { id: 'edgy', label: 'Edgy', icon: 'triangle-outline', color: '#8E44AD', description: 'Push boundaries' },
  { id: 'romantic', label: 'Romantic', icon: 'heart-outline', color: '#E91E63', description: 'Soft & feminine' },
];

const STYLE_INSPIRATIONS = [
  { id: 'trend_focused', label: 'Trend-Focused', description: 'Following latest fashion trends', icon: 'trending-up-outline', color: '#FF6B6B' },
  { id: 'inspired_by_vibe', label: 'Inspired by a Vibe', description: 'Following influencers and celebrities', icon: 'people-outline', color: '#4ECDC4' },
  { id: 'self_expressive', label: 'Self-Expressive', description: 'Creating my own unique style', icon: 'person-outline', color: '#F39C12' },
];

const STYLE_VIBES = {
  male: [
    { id: 'streetwear_casual', label: 'Streetwear casual', description: 'Urban and relaxed' },
    { id: 'minimal_clean', label: 'Minimal & clean', description: 'Simple and sophisticated' },
    { id: 'bold_statement', label: 'Bold & statement', description: 'Eye-catching looks' },
    { id: 'sporty_athleisure', label: 'Sporty athleisure', description: 'Active and comfortable' },
    { id: 'old_money', label: 'Old Money', description: 'Classic and refined' },
  ],
  female: [
    { id: 'streetwear_chic', label: 'Streetwear chic', description: 'Urban feminine' },
    { id: 'minimal_clean', label: 'Minimal & clean', description: 'Effortless elegance' },
    { id: 'soft_feminine', label: 'Soft & feminine', description: 'Romantic and delicate' },
    { id: 'sporty_athleisure', label: 'Sporty athleisure', description: 'Active lifestyle' },
    { id: 'bold_statement', label: 'Bold & statement', description: 'Confident and daring' },
  ],
  other: [
    { id: 'streetwear', label: 'Streetwear', description: 'Urban and trendy' },
    { id: 'minimal_clean', label: 'Minimal & clean', description: 'Clean and simple' },
    { id: 'expressive', label: 'Expressive', description: 'Uniquely you' },
    { id: 'sporty', label: 'Sporty', description: 'Active and comfortable' },
  ]
};

const STYLE_MESSAGES = [
  { id: 'confident', label: "I'm confident & bold" },
  { id: 'chill', label: "I'm chill AF" },
  { id: 'polished', label: "I'm polished & put-together" },
  { id: 'unpredictable', label: "I'm unpredictable, in a good way" },
];

interface User {
  id: string;
  email: string;
  name: string;
  gender?: string;
  city?: string;
  language: string;
  age?: number;
  profession?: string;
  body_shape?: string;
  skin_tone?: string;
  style_inspiration: string[];
  style_vibes: string[];
  style_message?: string;
  onboarding_completed: boolean;
}

interface WardrobeItem {
  id: string;
  user_id: string;
  image_base64: string;
  exact_item_name?: string;
  category?: string;
  color?: string;
  pattern?: string;
  fabric_type?: string;
  style?: string;
  tags: string[];
  created_at: string;
}

interface ChatMessage {
  id: string;
  user_id: string;
  message: string;
  is_user: boolean;
  timestamp: string;
  image_base64?: string;
  isTyping?: boolean; // For typing indicator
}

interface OutfitValidation {
  id: string;
  scores: {
    color_combo: number;
    fit: number;
    style: number;
    occasion: number;
  };
  overall_score: number;
  feedback: string;
  image_base64?: string;
}

export default function App() {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [currentTab, setCurrentTab] = useState('chat');
  const [isLogin, setIsLogin] = useState(true);
  const [loading, setLoading] = useState(false);
  
  // Auth form states
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [name, setName] = useState('');
  const [wardrobe, setWardrobe] = useState<WardrobeItem[]>([]);
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([]);
  const [chatInput, setChatInput] = useState('');
  const [chatImage, setChatImage] = useState<string | null>(null);
  
  // Onboarding states with visual cards
  const [showOnboarding, setShowOnboarding] = useState(false);
  const [onboardingStep, setOnboardingStep] = useState(1);
  const [onboardingData, setOnboardingData] = useState({
    name: '',
    gender: '',
    age_group: '',
    profession: '',
    body_shape: '',
    skin_tone: '',
    style_inspiration: '',
    style_vibe: '',
    style_message: '',
  });

  // Chat session management - fresh sessions each time
  const [chatSessionId, setChatSessionId] = useState('');
  
  // Additional auth form states (no duplicates)
  const [gender, setGender] = useState('');
  const [city, setCity] = useState('');
  const [language, setLanguage] = useState('english');

  // Validation states
  const [lastValidation, setLastValidation] = useState<OutfitValidation | null>(null);

  useEffect(() => {
    checkAuthStatus();
  }, []);

  useEffect(() => {
    if (user) {
      console.log('🎯 Checking onboarding status:', user.onboarding_completed);
      
      // Show onboarding only if explicitly false or undefined AND user has no basic profile data
      const needsOnboarding = !user.onboarding_completed && (
        !user.name || 
        !user.age || 
        !user.profession || 
        !user.body_shape || 
        !user.skin_tone
      );
      
      if (needsOnboarding) {
        console.log('🚪 Showing onboarding for new user');
        setShowOnboarding(true);
      } else {
        console.log('✅ User has completed onboarding, going to main app');
        setShowOnboarding(false);
      }
    }
  }, [user]);

  // Load chat history when switching to chat tab - persistent sessions
  useEffect(() => {
    if (currentTab === 'chat' && user && chatMessages.length === 0) {
      // Only load if chat is empty to avoid reloading when switching tabs
      loadChatHistory();
    }
  }, [currentTab]);

  // Load wardrobe when user and token are available
  useEffect(() => {
    if (user && token && currentTab === 'wardrobe') {
      loadWardrobe();
    }
  }, [user, token, currentTab]);

  const clearChatSession = () => {
    setChatMessages([]);
    setChatSessionId(Date.now().toString());
    setChatInput('');
    setChatImage(null);
  };

  const loadProfile = async () => {
    try {
      const response = await fetch(`${BACKEND_URL}/api/auth/me`, {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (response.ok) {
        const data = await response.json();
        setUser(data);
      }
    } catch (error) {
      console.error('Error loading profile:', error);
    }
  };

  const loadChatHistory = async () => {
    // Only load chat history if user is authenticated
    if (!token) {
      console.log('⚠️ Skipping chat history load - no authentication token');
      return;
    }
    
    try {
      const response = await fetch(`${BACKEND_URL}/api/chat/history`, {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (response.ok) {
        const messages = await response.json();
        setChatMessages(messages);
      } else if (response.status === 401) {
        console.log('⚠️ Unauthorized chat history access - clearing auth');
        await AsyncStorage.removeItem('token');
        setToken(null);
        setUser(null);
      }
    } catch (error) {
      console.error('Error loading chat history:', error);
    }
  };

  const startFreshChatSession = async () => {
    try {
      console.log('🆕 Starting fresh chat session...');
      
      // Clear frontend state immediately for instant feedback
      setChatMessages([]);
      setChatInput('');
      setChatImage(null);
      
      // Clear backend chat history
      if (token) {
        const response = await fetch(`${BACKEND_URL}/api/chat/clear`, {
          method: 'DELETE',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json',
          },
        });
        
        if (!response.ok) {
          console.warn('Backend chat clear failed, but frontend cleared');
        } else {
          console.log('✅ Backend chat history cleared');
        }
      } else {
        console.warn('No token available for backend clear');
      }
      
      console.log('✅ Fresh chat session started successfully');
      
    } catch (error) {
      console.error('Error starting fresh chat session:', error);
      // Still clear frontend even if backend fails
      setChatMessages([]);
      setChatInput('');
      setChatImage(null);
    }
  };

  const checkAuthStatus = async () => {
    try {
      const storedToken = await AsyncStorage.getItem('token');
      if (storedToken) {
        setToken(storedToken);
        
        const response = await fetch(`${BACKEND_URL}/api/auth/me`, {
          headers: {
            'Authorization': `Bearer ${storedToken}`,
            'Content-Type': 'application/json',
          },
        });
        
        if (response.ok) {
          const userData = await response.json();
          console.log('👤 User data received:', userData);
          console.log('🎯 Onboarding completed:', userData.onboarding_completed);
          setUser(userData);
          
          // Check if this is a fresh app session (app was reopened)
          await handleAppReopenBehavior();
        } else {
          await AsyncStorage.removeItem('token');
          setToken(null);
        }
      }
    } catch (error) {
      console.error('Error checking auth status:', error);
    }
  };

  const handleAppReopenBehavior = async () => {
    try {
      // Check if this is a new app session
      const lastSessionTime = await AsyncStorage.getItem('lastSessionTime');
      const currentTime = Date.now();
      
      // If no session recorded or more than 5 minutes passed, consider it a new session
      const sessionThreshold = 5 * 60 * 1000; // 5 minutes
      
      if (!lastSessionTime || (currentTime - parseInt(lastSessionTime)) > sessionThreshold) {
        // This is a new session - clear chat history
        console.log('🆕 New app session detected - clearing chat history');
        
        // Clear backend chat history (only if authenticated)
        if (token) {
          try {
            await fetch(`${BACKEND_URL}/api/chat/clear`, {
              method: 'DELETE',
              headers: {
                'Authorization': `Bearer ${token}`,
              },
            });
          } catch (error) {
            console.warn('Failed to clear backend chat history:', error);
          }
        }
        
        // Clear frontend chat state
        setChatMessages([]);
        setChatInput('');
        setChatImage(null);
        
      } else {
        // Continue existing session - load chat history
        loadChatHistory();
      }
      
      // Update session time
      await AsyncStorage.setItem('lastSessionTime', currentTime.toString());
      
    } catch (error) {
      console.error('Error handling app reopen behavior:', error);
      // Fallback: load existing chat history
      loadChatHistory();
    }
  };

  // Removed duplicate handleAuth function - kept the one with better debugging

  const completeOnboarding = async () => {
    setLoading(true);
    try {
      const response = await fetch(`${BACKEND_URL}/api/auth/onboarding`, {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          name: onboardingData.name,
          gender: onboardingData.gender,
          age: onboardingData.age_group ? parseInt(onboardingData.age_group.split('-')[0]) : null,
          profession: onboardingData.profession,
          body_shape: onboardingData.body_shape,
          skin_tone: onboardingData.skin_tone,
          style_inspiration: onboardingData.style_inspiration,
          style_vibe: onboardingData.style_vibe,
          style_message: onboardingData.style_message,
        }),
      });

      if (response.ok) {
        const updatedUser = await response.json();
        setUser(updatedUser);
        setShowOnboarding(false);
        setCurrentTab('chat');
        clearChatSession();
      } else {
        Alert.alert('Error', 'Failed to complete onboarding');
      }
    } catch (error) {
      console.error('Onboarding error:', error);
      Alert.alert('Error', 'Network error. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const logout = async () => {
    await AsyncStorage.removeItem('token');
    setUser(null);
    setToken(null);
    setCurrentTab('chat');
    setShowOnboarding(false);
  };

  const loadWardrobe = async () => {
    // Only load wardrobe if user is authenticated
    if (!token) {
      console.log('⚠️ Skipping wardrobe load - no authentication token');
      return;
    }
    
    try {
      const response = await fetch(`${BACKEND_URL}/api/wardrobe`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });
      
      if (response.ok) {
        const data = await response.json();
        // Backend returns {items: [...]} format
        const wardrobeItems = data.items || data;
        // Ensure wardrobe is always an array
        setWardrobe(Array.isArray(wardrobeItems) ? wardrobeItems : []);
      } else if (response.status === 401) {
        console.log('⚠️ Unauthorized wardrobe access - clearing auth');
        await AsyncStorage.removeItem('token');
        setToken(null);
        setUser(null);
      }
    } catch (error) {
      console.error('Error loading wardrobe:', error);
    }
  };

  const [selectedCategoryFilter, setSelectedCategoryFilter] = useState<string>('all');

  const addWardrobeItems = async () => {
    try {
      const { status } = await ImagePicker.requestMediaLibraryPermissionsAsync();
      if (status !== 'granted') {
        Alert.alert('Permission needed', 'Please grant camera roll permissions to use this feature.');
        return;
      }

      setLoading(true);
      const result = await ImagePicker.launchImageLibraryAsync({
        mediaTypes: [ImagePicker.MediaTypeOptions.Images],
        allowsMultipleSelection: false,
        quality: 0.3,  // Reduced quality to keep image size small
        base64: true,
      });

      if (!result.canceled && result.assets && result.assets[0]) {
        const asset = result.assets[0];
        if (asset.base64) {
          console.log('📷 Processing image upload...');
          console.log('Image size (base64):', asset.base64.length);
          
          // Ensure we have a valid base64 string
          const base64Data = asset.base64.replace(/^data:image\/[a-z]+;base64,/, '');
          
          // Get file extension from URI if available
          const fileExtension = asset.uri ? asset.uri.split('.').pop()?.toLowerCase() : 'jpeg';
          const mimeType = fileExtension === 'png' ? 'image/png' : 'image/jpeg';
          
          const imageDataUrl = `data:${mimeType};base64,${base64Data}`;
          
          console.log('📡 Sending to backend:', `${BACKEND_URL}/api/wardrobe`);
          
          const response = await fetch(`${BACKEND_URL}/api/wardrobe`, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
              'Authorization': `Bearer ${token}`,
            },
            body: JSON.stringify({
              image_base64: imageDataUrl,
              manual_tags: [],
            }),
          });

          if (response.ok) {
            const result = await response.json();
            loadWardrobe(); // Refresh wardrobe
            
            // Show success message
            const itemCount = result.items_added || 1;
            Alert.alert(
              '🎉 Upload Complete!', 
              `Successfully processed and added ${itemCount} item(s) to your wardrobe!\n\n✨ Each item has been extracted, background removed, and styled professionally.`
            );
          } else {
            throw new Error('Failed to add item');
          }
        }
      }
    } catch (error) {
      console.error('Error adding wardrobe items:', error);
      Alert.alert('Error', 'Failed to add items to wardrobe');
    } finally {
      setLoading(false);
    }
  };

  // Removed placeholder function as requested

  const deleteWardrobeItem = async (itemId: string) => {
    try {
      console.log(`🗑️ Deleting item: ${itemId}`);
      
      // Immediately update UI - optimistic delete
      setWardrobe(prevWardrobe => prevWardrobe.filter(item => item.id !== itemId));
      
      if (!token) {
        throw new Error('No authentication token');
      }
      
      const response = await fetch(`${BACKEND_URL}/api/wardrobe/${itemId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (response.ok) {
        console.log('✅ Item deleted successfully');
      } else {
        console.error(`Delete failed: ${response.status}`);
        // If delete failed, revert the optimistic update
        loadWardrobe();
        Alert.alert('Error', 'Failed to delete item - restoring item');
      }
    } catch (error) {
      // If delete failed, revert the optimistic update
      console.error('Error deleting wardrobe item:', error);
      loadWardrobe();
      Alert.alert('Error', 'Failed to delete item - restoring item');
    }
  };

  // Group wardrobe items by category
  const getGroupedWardrobe = () => {
    const grouped: { [key: string]: WardrobeItem[] } = {};
    // Safety check: ensure wardrobe is an array
    if (Array.isArray(wardrobe)) {
      wardrobe.forEach(item => {
        const category = item.category || 'Other';
        if (!grouped[category]) {
          grouped[category] = [];
        }
        grouped[category].push(item);
      });
    }
    return grouped;
  };

  // Get available categories for filtering
  const getAvailableCategories = () => {
    const categories = new Set<string>();
    // Safety check: ensure wardrobe is an array
    if (Array.isArray(wardrobe)) {
      wardrobe.forEach(item => {
        categories.add(item.category || 'Other');
      });
    }
    return Array.from(categories).sort();
  };

  // Filter wardrobe by selected category
  const getFilteredWardrobe = () => {
    if (selectedCategoryFilter === 'all') {
      return getGroupedWardrobe();
    }
    
    const allGrouped = getGroupedWardrobe();
    const filtered: { [key: string]: WardrobeItem[] } = {};
    
    if (allGrouped[selectedCategoryFilter]) {
      filtered[selectedCategoryFilter] = allGrouped[selectedCategoryFilter];
    }
    
    return filtered;
  };

  const sendMessage = async () => {
    if (!chatInput.trim() && !chatImage) return;
    
    // Add user message to UI immediately
    const userMessage: ChatMessage = {
      id: Date.now().toString(),
      user_id: user!.id,
      message: chatInput || 'Please analyze this image',
      is_user: true,
      timestamp: new Date().toISOString(),
      image_base64: chatImage || undefined,
    };
    
    setChatMessages(prev => [...prev, userMessage]);
    
    // Add loading message for AI analysis if there's an image
    let loadingMessage: ChatMessage | null = null;
    if (chatImage) {
      loadingMessage = {
        id: 'loading-' + Date.now(),
        user_id: user!.id,
        message: '🔄 Analyzing your image and creating style suggestions...',
        is_user: false,
        timestamp: new Date().toISOString(),
      };
      setChatMessages(prev => [...prev, loadingMessage]);
      
      await handleItemExtractionPermission(chatImage, chatInput);
    }
    
    const currentInput = chatInput;
    const currentImage = chatImage;
    setChatInput('');
    setChatImage(null);
    
    setLoading(true);
    
    // Add typing indicator
    const typingMessage: ChatMessage = {
      id: 'typing-' + Date.now(),
      user_id: user!.id,
      message: '...',
      is_user: false,
      timestamp: new Date().toISOString(),
      isTyping: true,
    };
    setChatMessages(prev => [...prev.filter(msg => !msg.id.startsWith('loading-')), typingMessage]);
    
    try {
      const response = await fetch(`${BACKEND_URL}/api/chat`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: currentInput || 'Please analyze this image',
          image_base64: currentImage ? `data:image/jpeg;base64,${currentImage}` : undefined,
        }),
      });

      const data = await response.json();

      if (response.ok) {
        // Remove typing indicator
        setChatMessages(prev => prev.filter(msg => !msg.id.startsWith('typing-') && !msg.id.startsWith('loading-')));
        
        // Handle chunked messages - add them sequentially with delays
        const messageChunks = data.messages || [data.message]; // Support both new and old format
        
        for (let i = 0; i < messageChunks.length; i++) {
          // Add slight delay between chunks for natural feel (except first one)
          if (i > 0) {
            await new Promise(resolve => setTimeout(resolve, 600)); // 600ms delay between chunks
          }
          
          const aiMessage: ChatMessage = {
            id: data.message_ids ? data.message_ids[i] : (Date.now() + i).toString(),
            user_id: user!.id,
            message: messageChunks[i],
            is_user: false,
            timestamp: new Date().toISOString(),
          };
          
          setChatMessages(prev => [...prev, aiMessage]);
        }
      } else {
        // Remove typing indicator on error
        setChatMessages(prev => prev.filter(msg => !msg.id.startsWith('typing-') && !msg.id.startsWith('loading-')));
        Alert.alert('Error', data.detail || 'Failed to send message');
      }
    } catch (error) {
      console.error('Error sending message:', error);
      // Remove typing indicator on network error
      setChatMessages(prev => prev.filter(msg => !msg.id.startsWith('typing-') && !msg.id.startsWith('loading-')));
      Alert.alert('Network Error', 'Please check your internet connection and try again');
    } finally {
      setLoading(false);
    }
  };

  const [debugError, setDebugError] = useState('');

  const handleAuth = async () => {
    console.log('🚀 LOGIN ATTEMPT STARTED');
    console.log('Email:', email);
    console.log('Password length:', password.length);
    console.log('IsLogin:', isLogin);
    console.log('Backend URL:', BACKEND_URL);
    
    setDebugError(''); // Clear previous errors
    
    if (!email || !password) {
      const errorMsg = 'Please fill in all fields';
      setDebugError(errorMsg);
      Alert.alert('Error', errorMsg);
      return;
    }

    if (!isLogin && !name) {
      const errorMsg = 'Name is required for signup';
      setDebugError(errorMsg);
      Alert.alert('Error', errorMsg);
      return;
    }

    setLoading(true);
    try {
      const endpoint = isLogin ? '/api/auth/login' : '/api/auth/register';
      const body = isLogin 
        ? { email, password }
        : { email, password, name, gender, city, language };

      console.log('📡 Making request to:', `${BACKEND_URL}${endpoint}`);
      console.log('📦 Request body:', body);

      const response = await fetch(`${BACKEND_URL}${endpoint}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(body),
      });

      console.log('📬 Response status:', response.status);
      
      const data = await response.json();
      console.log('📄 Response data:', data);

      if (response.ok) {
        console.log('✅ AUTH SUCCESS!');
        await AsyncStorage.setItem('token', data.access_token);
        setToken(data.access_token);
        setUser(data.user);
        // Clear form
        setEmail('');
        setPassword('');
        setName('');
        setGender('');
        setCity('');
        setDebugError('SUCCESS! Login completed');
      } else {
        const errorMsg = data.detail || `Authentication failed (${response.status})`;
        console.log('❌ AUTH FAILED:', errorMsg);
        setDebugError(`ERROR ${response.status}: ${errorMsg}`);
        Alert.alert('Authentication Failed', errorMsg);
      }
    } catch (error) {
      console.error('💥 AUTH ERROR:', error);
      const errorMsg = `Network error: ${error.message}`;
      setDebugError(errorMsg);
      Alert.alert('Network Error', errorMsg);
    } finally {
      setLoading(false);
    }
  };

  const handleItemExtractionPermission = async (imageBase64: string, context: string) => {
    try {
      Alert.alert(
        '🔍 Extract Wardrobe Items',
        'Would you like me to analyze this photo and add any visible clothing items to your wardrobe?\n\n✨ I can detect and process multiple items automatically!',
        [
          {
            text: 'Not Now',
            style: 'cancel',
          },
          {
            text: '✅ Yes, Extract Items',
            onPress: async () => {
              try {
                setLoading(true);
                
                const response = await fetch(`${BACKEND_URL}/api/wardrobe`, {
                  method: 'POST',
                  headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`,
                  },
                  body: JSON.stringify({
                    image_base64: imageBase64,
                    manual_tags: ['chat-extracted', context.slice(0, 20)], // Add context as tag
                  }),
                });

                if (response.ok) {
                  const result = await response.json();
                  loadWardrobe(); // Refresh wardrobe to show new items
                  
                  // Show success message
                  Alert.alert(
                    '🎉 Items Extracted!', 
                    `Successfully detected and added ${result.items_added} clothing item(s) to your wardrobe!\n\n📸 Each item has been processed with background removal and complementary styling.`
                  );
                } else {
                  Alert.alert('Error', 'Failed to extract items from the image');
                }
              } catch (error) {
                console.error('Error extracting items:', error);
                Alert.alert('Error', 'Failed to extract wardrobe items');
              } finally {
                setLoading(false);
              }
            },
          },
        ],
        { cancelable: true }
      );
    } catch (error) {
      console.error('Error handling item extraction permission:', error);
    }
  };

  const selectChatImage = async () => {
    try {
      console.log('📷 Selecting chat image...');
      
      const result = await ImagePicker.launchImageLibraryAsync({
        mediaTypes: [ImagePicker.MediaTypeOptions.Images],
        allowsEditing: true,
        aspect: [3, 4],
        quality: 0.7,
        base64: true,
        exif: false,
        // Support all image formats including HEIC
      });

      if (!result.canceled && result.assets[0]?.base64) {
        const asset = result.assets[0];
        console.log('📷 Image selected, size:', asset.base64.length);
        
        // Clean base64 string and validate it
        const base64Data = asset.base64.replace(/^data:image\/[a-z]+;base64,/, '');
        
        if (base64Data && base64Data.length > 0) {
          setChatImage(base64Data);
          console.log('✅ Chat image set successfully');
        } else {
          throw new Error('Invalid base64 data');
        }
      }
    } catch (error) {
      console.error('Error selecting chat image:', error);
      Alert.alert('Error', 'Failed to select image. Please try again.');
    }
  };

  const validateOutfit = async () => {
    try {
      console.log('👔 Starting outfit validation...');
      
      const result = await ImagePicker.launchImageLibraryAsync({
        mediaTypes: [ImagePicker.MediaTypeOptions.Images],
        allowsEditing: true,
        aspect: [3, 4],
        quality: 0.8,
        base64: true,
        exif: false,
        // Support all image formats including HEIC
      });

      if (!result.canceled && result.assets[0]?.base64) {
        const asset = result.assets[0];
        console.log('👔 Outfit image selected, size:', asset.base64.length);
        
        setLoading(true);
        
        // Clean and prepare base64 data
        const base64Data = asset.base64.replace(/^data:image\/[a-z]+;base64,/, '');
        const fileExtension = asset.uri ? asset.uri.split('.').pop()?.toLowerCase() : 'jpeg';
        const mimeType = fileExtension === 'png' ? 'image/png' : 'image/jpeg';
        const imageBase64 = `data:${mimeType};base64,${base64Data}`;
        
        console.log('📡 Validating outfit with backend...');
        
        const response = await fetch(`${BACKEND_URL}/api/validate-outfit`, {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            image_base64: imageBase64,
          }),
        });

        if (response.ok) {
          const validation = await response.json();
          setLastValidation(validation);
          
          // Ask for permission to extract items after successful validation
          await handleOutfitExtractionPermission(imageBase64);
        } else {
          Alert.alert('Error', 'Failed to validate outfit');
        }
      }
    } catch (error) {
      console.error('Error validating outfit:', error);
      Alert.alert('Error', 'Failed to validate outfit');
    } finally {
      setLoading(false);
    }
  };

  const handleOutfitExtractionPermission = async (imageBase64: string) => {
    try {
      Alert.alert(
        '👗 Add Items to Wardrobe',
        'Great outfit! Would you like me to extract and add the individual clothing items from this outfit to your wardrobe?\n\n🎯 Perfect for building your style collection!',
        [
          {
            text: 'Maybe Later',
            style: 'cancel',
          },
          {
            text: '✨ Yes, Add Items',
            onPress: async () => {
              try {
                setLoading(true);
                
                const response = await fetch(`${BACKEND_URL}/api/wardrobe`, {
                  method: 'POST',
                  headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`,
                  },
                  body: JSON.stringify({
                    image_base64: imageBase64,
                    manual_tags: ['validated-outfit', 'outfit-extract'],
                  }),
                });

                if (response.ok) {
                  const result = await response.json();
                  loadWardrobe(); // Refresh wardrobe
                  
                  // Show success message
                  Alert.alert(
                    '🎉 Items Added!', 
                    `Successfully extracted and added ${result.items_added} item(s) from your outfit to your wardrobe!\n\n💫 Each piece is now available for future styling.`
                  );
                } else {
                  Alert.alert('Error', 'Failed to extract items from outfit');
                }
              } catch (error) {
                console.error('Error extracting outfit items:', error);
                Alert.alert('Error', 'Failed to extract outfit items');
              } finally {
                setLoading(false);
              }
            },
          },
        ],
        { cancelable: true }
      );
    } catch (error) {
      console.error('Error handling outfit extraction permission:', error);
    }
  };

  // Visual Onboarding Screen with Card Selection
  if (showOnboarding && user) {
    return (
      <Modal visible={true} animationType="slide">
        <SafeAreaView style={styles.container}>
          <KeyboardAvoidingView style={{ flex: 1 }} behavior={Platform.OS === 'ios' ? 'padding' : 'height'}>
            <ScrollView contentContainerStyle={styles.onboardingContainer}>
              <View style={styles.onboardingHeader}>
                <Text style={styles.onboardingTitle}>Let's Create Your Style Profile!</Text>
                <Text style={styles.onboardingSubtitle}>Step {onboardingStep} of 6</Text>
                <View style={styles.progressBar}>
                  <View style={[styles.progressFill, { width: `${(onboardingStep / 6) * 100}%` }]} />
                </View>
              </View>

              {/* Step 1: Name + Gender + Age + Occupation (Combined Screen) */}
              {onboardingStep === 1 && (
                <ScrollView style={styles.combinedOnboardingStep} showsVerticalScrollIndicator={false}>
                  <Text style={styles.welcomeTitle}>Hey there, Style Icon! ✨</Text>
                  <Text style={styles.welcomeSubtitle}>Let's get to know you better</Text>
                  
                  {/* Name Input */}
                  <View style={styles.formSection}>
                    <Text style={styles.sectionLabel}>What's your name?</Text>
                    <TextInput
                      style={styles.textInput}
                      placeholder="Enter your name"
                      value={onboardingData.name}
                      onChangeText={(text) => setOnboardingData({...onboardingData, name: text})}
                      autoCapitalize="words"
                    />
                  </View>

                  {/* Gender Selection */}
                  <View style={styles.formSection}>
                    <Text style={styles.sectionLabel}>Gender</Text>
                    <View style={styles.buttonRow}>
                      {GENDER_OPTIONS.map((option) => (
                        <TouchableOpacity
                          key={option.id}
                          style={[
                            styles.optionButton,
                            onboardingData.gender === option.id && styles.selectedOptionButton
                          ]}
                          onPress={() => setOnboardingData({...onboardingData, gender: option.id})}
                        >
                          <Text style={[
                            styles.optionButtonText,
                            onboardingData.gender === option.id && styles.selectedOptionButtonText
                          ]}>
                            {option.label}
                          </Text>
                        </TouchableOpacity>
                      ))}
                    </View>
                  </View>

                  {/* Age Selection */}
                  <View style={styles.formSection}>
                    <Text style={styles.sectionLabel}>Age</Text>
                    <View style={styles.buttonRow}>
                      {AGE_GROUPS.map((option) => (
                        <TouchableOpacity
                          key={option.id}
                          style={[
                            styles.optionButton,
                            onboardingData.age_group === option.id && styles.selectedOptionButton
                          ]}
                          onPress={() => setOnboardingData({...onboardingData, age_group: option.id})}
                        >
                          <Text style={[
                            styles.optionButtonText,
                            onboardingData.age_group === option.id && styles.selectedOptionButtonText
                          ]}>
                            {option.label}
                          </Text>
                        </TouchableOpacity>
                      ))}
                    </View>
                  </View>

                  {/* Occupation Selection */}
                  <View style={styles.formSection}>
                    <Text style={styles.sectionLabel}>Occupation</Text>
                    <View style={styles.buttonRow}>
                      {PROFESSIONS.map((option) => (
                        <TouchableOpacity
                          key={option.id}
                          style={[
                            styles.optionButton,
                            onboardingData.profession === option.id && styles.selectedOptionButton
                          ]}
                          onPress={() => setOnboardingData({...onboardingData, profession: option.id})}
                        >
                          <Ionicons name={option.icon as any} size={20} color={onboardingData.profession === option.id ? '#FFF' : '#666'} style={{ marginRight: 6 }} />
                          <Text style={[
                            styles.optionButtonText,
                            onboardingData.profession === option.id && styles.selectedOptionButtonText
                          ]}>
                            {option.label}
                          </Text>
                        </TouchableOpacity>
                      ))}
                    </View>
                  </View>
                </ScrollView>
              )}

              {/* Step 2: Body Shape */}
              {onboardingStep === 2 && (
                <View style={styles.onboardingStep}>
                  <Text style={styles.stepTitle}>What's your body shape?</Text>
                  <Text style={styles.stepSubtitle}>This helps me suggest the most flattering styles</Text>
                  
                  <View style={styles.cardGrid}>
                    {(BODY_SHAPES[onboardingData.gender as keyof typeof BODY_SHAPES] || BODY_SHAPES.other).map((option) => (
                      <TouchableOpacity
                        key={option.id}
                        style={[
                          styles.bodyShapeCard,
                          onboardingData.body_shape === option.id && styles.selectedCard
                        ]}
                        onPress={() => setOnboardingData({...onboardingData, body_shape: option.id})}
                      >
                        <Image 
                          source={{ uri: option.image }} 
                          style={styles.bodyShapeImage}
                          resizeMode="contain"
                        />
                        <Text style={styles.cardLabel}>{option.label}</Text>
                      </TouchableOpacity>
                    ))}
                  </View>
                </View>
              )}

              {/* Step 3: Skin Tone */}
              {onboardingStep === 3 && (
                <View style={styles.onboardingStep}>
                  <Text style={styles.stepTitle}>What's your skin tone?</Text>
                  <Text style={styles.stepSubtitle}>Colors that complement your natural beauty</Text>
                  
                  <View style={styles.skinToneGrid}>
                    {SKIN_TONES.map((tone) => (
                      <TouchableOpacity
                        key={tone.id}
                        style={[
                          styles.skinToneCard,
                          { backgroundColor: tone.color },
                          onboardingData.skin_tone === tone.id && styles.selectedSkinTone
                        ]}
                        onPress={() => setOnboardingData({...onboardingData, skin_tone: tone.id})}
                      >
                        <Text style={styles.skinToneLabel}>{tone.label}</Text>
                      </TouchableOpacity>

              {/* Step 4: Style Inspiration */}
              {onboardingStep === 4 && (
                <View style={styles.onboardingStep}>
                  <Text style={styles.stepTitle}>What inspires your style?</Text>
                  <Text style={styles.stepSubtitle}>How do you discover new looks?</Text>
                  
                  <View style={styles.styleInspirationGrid}>
                    {STYLE_INSPIRATIONS.map((option) => (
                      <TouchableOpacity
                        key={option.id}
                        style={[
                          styles.styleInspirationCard,
                          onboardingData.style_inspiration === option.id && styles.selectedStyleCard
                        ]}
                        onPress={() => setOnboardingData({...onboardingData, style_inspiration: option.id})}
                      >
                        <Image 
                          source={{ 
                            uri: option.id === 'trend_focused' 
                              ? 'https://customer-assets.emergentagent.com/job_stylistai/artifacts/r4dr5lw5_Trends%404x.png'
                              : option.id === 'inspired_by_vibe' 
                                ? (onboardingData.gender === 'male' 
                                  ? 'https://customer-assets.emergentagent.com/job_stylistai/artifacts/d4hww85j_Male%20Inspo%404x.png'
                                  : 'https://customer-assets.emergentagent.com/job_stylistai/artifacts/iw70gpmz_Female%20Inspo%404x.png')
                                : (onboardingData.gender === 'male'
                                  ? 'https://customer-assets.emergentagent.com/job_stylistai/artifacts/e570og4o_Adam%201%404x.png'
                                  : 'https://customer-assets.emergentagent.com/job_stylistai/artifacts/89anhi7k_Geet%202%404x.png')
                          }} 
                          style={styles.styleInspirationImage}
                          resizeMode="cover"
                        />
                        <View style={styles.styleInspirationTextContainer}>
                          <Text style={styles.styleInspirationLabel}>{option.label}</Text>
                          <Text style={styles.styleInspirationDescription}>{option.description}</Text>
                        </View>
                      </TouchableOpacity>
                    ))}
                  </View>
                </View>
              )}

              {/* Step 5: Style Vibe */}
              {onboardingStep === 5 && (
                <View style={styles.onboardingStep}>
                  <Text style={styles.stepTitle}>What's your style vibe?</Text>
                  <Text style={styles.stepSubtitle}>Choose the aesthetic that speaks to you</Text>
                  
                  <ScrollView style={styles.styleVibeScroll} showsVerticalScrollIndicator={false}>
                    {(STYLE_VIBES[onboardingData.gender as keyof typeof STYLE_VIBES] || STYLE_VIBES.other).map((option, index) => {
                      // Map style vibes to images
                      const getStyleVibeImage = () => {
                        if (onboardingData.gender === 'female') {
                          const femaleImages = [
                            'https://customer-assets.emergentagent.com/job_stylistai/artifacts/4r6dijid_Frame%202087328105.png', // Streetwear chic
                            'https://customer-assets.emergentagent.com/job_stylistai/artifacts/taln6og3_Frame%202087328106.png', // Minimal & clean
                            'https://customer-assets.emergentagent.com/job_stylistai/artifacts/y4w156f0_Frame%202087328107.png', // Soft & feminine
                            'https://customer-assets.emergentagent.com/job_stylistai/artifacts/uodqmnf6_Frame%202087328105-1.png', // Sporty athleisure
                            'https://customer-assets.emergentagent.com/job_stylistai/artifacts/r41svisl_Frame%202087328106-1.png', // Bold & statement
                          ];
                          return femaleImages[index];
                        } else {
                          const maleImages = [
                            'https://customer-assets.emergentagent.com/job_stylistai/artifacts/9uydlrew_Frame%202087328105.png', // Streetwear casual
                            'https://customer-assets.emergentagent.com/job_stylistai/artifacts/lurvtpev_Frame%202087328106.png', // Minimal & clean
                            'https://customer-assets.emergentagent.com/job_stylistai/artifacts/izvuvymm_Frame%202087328107.png', // Bold & statement
                            'https://customer-assets.emergentagent.com/job_stylistai/artifacts/2kco8shh_Frame%202087328105-1.png', // Sporty athleisure
                            'https://customer-assets.emergentagent.com/job_stylistai/artifacts/xn4hfg1x_Frame%202087328106-1.png', // Old Money
                          ];
                          return maleImages[index];
                        }
                      };
                      
                      return (
                        <TouchableOpacity
                          key={option.id}
                          style={[
                            styles.styleVibeCard,
                            onboardingData.style_vibe === option.id && styles.selectedStyleVibeCard
                          ]}
                          onPress={() => setOnboardingData({...onboardingData, style_vibe: option.id})}
                        >
                          <Image 
                            source={{ uri: getStyleVibeImage() }} 
                            style={styles.styleVibeImage}
                            resizeMode="cover"
                          />
                          <View style={styles.styleVibeTextContainer}>
                            <Text style={styles.styleVibeLabel}>{option.label}</Text>
                            <Text style={styles.styleVibeDescription}>{option.description}</Text>
                          </View>
                          {onboardingData.style_vibe === option.id && (
                            <View style={styles.styleVibeCheckmark}>
                              <Ionicons name="checkmark-circle" size={28} color="#007AFF" />
                            </View>
                          )}
                        </TouchableOpacity>
                      );
                    })}

              {/* Step 6: Style Message */}
              {onboardingStep === 6 && (
                <View style={styles.onboardingStep}>
                  <Text style={styles.stepTitle}>What's your style motto?</Text>
                  <Text style={styles.stepSubtitle}>Choose the statement that resonates with you</Text>
                  
                  <View style={styles.styleMessageGrid}>
                    {STYLE_MESSAGES.map((option) => (
                      <TouchableOpacity
                        key={option.id}
                        style={[
                          styles.styleMessageCard,
                          onboardingData.style_message === option.id && styles.selectedStyleMessageCard
                        ]}
                        onPress={() => setOnboardingData({...onboardingData, style_message: option.id})}
                      >
                        <Text style={styles.styleMessageLabel}>{option.label}</Text>
                        {onboardingData.style_message === option.id && (
                          <Ionicons name="checkmark-circle" size={24} color="#007AFF" />
                        )}
                      </TouchableOpacity>
                    ))}
                  </View>
                </View>
              )}

                  </ScrollView>
                </View>
              )}

                    ))}
                  </View>
                </View>
              )}

              {/* Navigation Buttons */}
              <View style={styles.onboardingButtons}>
                {onboardingStep > 1 && (
                  <TouchableOpacity
                    style={styles.backButton}
                    onPress={() => setOnboardingStep(onboardingStep - 1)}
                  >
                    <Ionicons name="arrow-back" size={20} color="#007AFF" />
                    <Text style={styles.backButtonText}>Back</Text>
                  </TouchableOpacity>
                )}
                
                <TouchableOpacity
                  style={[
                    styles.nextButton,
                    onboardingStep === 1 ? { flex: 1 } : {},
                    loading && styles.disabledButton,
                  ]}
                  onPress={() => {
                    if (onboardingStep < 8) {
                      setOnboardingStep(onboardingStep + 1);
                    } else {
                      completeOnboarding();
                    }
                  }}
                  disabled={loading}
                >
                  {loading ? (
                    <ActivityIndicator color="white" />
                  ) : (
                    <>
                      <Text style={styles.nextButtonText}>
                        {onboardingStep === 8 ? 'Complete Profile ✨' : 'Continue'}
                      </Text>
                      <Ionicons name="arrow-forward" size={20} color="white" />
                    </>
                  )}
                </TouchableOpacity>
              </View>
            </ScrollView>
          </KeyboardAvoidingView>
        </SafeAreaView>
      </Modal>
    );
  }

  // Auth Screen
  if (!user) {
    return (
      <SafeAreaView style={styles.container}>
        <StatusBar barStyle="dark-content" backgroundColor="#f8f9fa" />
        <KeyboardAvoidingView 
          style={styles.authContainer}
          behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
        >
          <ScrollView contentContainerStyle={styles.authScrollView}>
            <View style={styles.authHeader}>
              <View style={styles.logoContainer}>
                <Ionicons name="sparkles" size={48} color="#007AFF" />
              </View>
              <Text style={styles.appTitle}>AI Stylist</Text>
              <Text style={styles.appSubtitle}>Your Personal Fashion Assistant</Text>
              <Text style={styles.appTagline}>Discover your perfect style with AI-powered wardrobe management</Text>
            </View>

            <View style={styles.authToggle}>
              <TouchableOpacity
                style={[styles.toggleButton, isLogin && styles.activeToggle]}
                onPress={() => setIsLogin(true)}
              >
                <Text style={[styles.toggleText, isLogin && styles.activeToggleText]}>Login</Text>
              </TouchableOpacity>
              <TouchableOpacity
                style={[styles.toggleButton, !isLogin && styles.activeToggle]}
                onPress={() => setIsLogin(false)}
              >
                <Text style={[styles.toggleText, !isLogin && styles.activeToggleText]}>Sign Up</Text>
              </TouchableOpacity>
            </View>

            <View style={styles.form}>
              {/* DEBUG ERROR DISPLAY */}
              {debugError ? (
                <View style={styles.debugContainer}>
                  <Text style={styles.debugText}>🐛 DEBUG: {debugError}</Text>
                </View>
              ) : null}
              
              {!isLogin && (
                <TextInput
                  style={styles.input}
                  placeholder="Full Name"
                  value={name}
                  onChangeText={setName}
                  autoCapitalize="words"
                />
              )}
              
              <TextInput
                style={styles.input}
                placeholder="Email"
                value={email}
                onChangeText={setEmail}
                keyboardType="email-address"
                autoCapitalize="none"
              />
              
              <TextInput
                style={styles.input}
                placeholder="Password"
                value={password}
                onChangeText={setPassword}
                secureTextEntry
              />
              
              {!isLogin && (
                <>
                  <TextInput
                    style={styles.input}
                    placeholder="Gender (Optional)"
                    value={gender}
                    onChangeText={setGender}
                  />
                  
                  <TextInput
                    style={styles.input}
                    placeholder="City (Optional)"
                    value={city}
                    onChangeText={setCity}
                  />
                  
                  <View style={styles.languageSelector}>
                    <Text style={styles.languageLabel}>Language:</Text>
                    <View style={styles.languageButtons}>
                      <TouchableOpacity
                        style={[styles.langButton, language === 'english' && styles.activeLang]}
                        onPress={() => setLanguage('english')}
                      >
                        <Text style={[styles.langText, language === 'english' && styles.activeLangText]}>English</Text>
                      </TouchableOpacity>
                      <TouchableOpacity
                        style={[styles.langButton, language === 'hindi' && styles.activeLang]}
                        onPress={() => setLanguage('hindi')}
                      >
                        <Text style={[styles.langText, language === 'hindi' && styles.activeLangText]}>हिंदी</Text>
                      </TouchableOpacity>
                    </View>
                  </View>
                </>
              )}
              
              <TouchableOpacity
                style={[styles.authButton, loading && styles.disabledButton]}
                onPress={handleAuth}
                disabled={loading}
              >
                {loading ? (
                  <ActivityIndicator color="white" />
                ) : (
                  <Text style={styles.authButtonText}>
                    {isLogin ? 'Login' : 'Create Account'}
                  </Text>
                )}
              </TouchableOpacity>
            </View>
          </ScrollView>
        </KeyboardAvoidingView>
      </SafeAreaView>
    );
  }

  // Removed duplicate auth screen - using the first one with proper debug features

  // Main App with Fresh Chat Sessions
  return (
    <SafeAreaView style={styles.container}>
      <StatusBar barStyle="dark-content" backgroundColor="#f8f9fa" />
      
      {/* Header */}
      <View style={styles.header}>
        <Text style={styles.headerTitle}>AI Stylist</Text>
        <TouchableOpacity onPress={logout} style={styles.logoutButton}>
          <Ionicons name="log-out-outline" size={24} color="#666" />
        </TouchableOpacity>
      </View>

      {/* Tab Navigation */}
      <View style={styles.tabBar}>
        <TouchableOpacity
          style={[styles.tab, currentTab === 'chat' && styles.activeTab]}
          onPress={() => setCurrentTab('chat')}
        >
          <Ionicons name="chatbubble-outline" size={24} color={currentTab === 'chat' ? '#007AFF' : '#666'} />
          <Text style={[styles.tabText, currentTab === 'chat' && styles.activeTabText]}>Chat</Text>
        </TouchableOpacity>
        
        <TouchableOpacity
          style={[styles.tab, currentTab === 'wardrobe' && styles.activeTab]}
          onPress={() => setCurrentTab('wardrobe')}
        >
          <Ionicons name="shirt-outline" size={24} color={currentTab === 'wardrobe' ? '#007AFF' : '#666'} />
          <Text style={[styles.tabText, currentTab === 'wardrobe' && styles.activeTabText]}>Wardrobe</Text>
        </TouchableOpacity>
        
        <TouchableOpacity
          style={[styles.tab, currentTab === 'validate' && styles.activeTab]}
          onPress={() => setCurrentTab('validate')}
        >
          <Ionicons name="checkmark-circle-outline" size={24} color={currentTab === 'validate' ? '#007AFF' : '#666'} />
          <Text style={[styles.tabText, currentTab === 'validate' && styles.activeTabText]}>Validate</Text>
        </TouchableOpacity>
        
        <TouchableOpacity
          style={[styles.tab, currentTab === 'profile' && styles.activeTab]}
          onPress={() => setCurrentTab('profile')}
        >
          <Ionicons name="person-outline" size={24} color={currentTab === 'profile' ? '#007AFF' : '#666'} />
          <Text style={[styles.tabText, currentTab === 'profile' && styles.activeTabText]}>Profile</Text>
        </TouchableOpacity>
      </View>

      {/* Content */}
      <View style={styles.content}>
        {currentTab === 'chat' && (
          <KeyboardAvoidingView 
            style={styles.chatContainer}
            behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
          >
            <View style={styles.chatHeader}>
              <Text style={styles.chatHeaderTitle}>Chat with Maya</Text>
              <TouchableOpacity
                style={styles.newChatButton}
                onPress={startFreshChatSession}
              >
                <Ionicons name="add" size={20} color="#007AFF" />
                <Text style={styles.newChatText}>New Chat</Text>
              </TouchableOpacity>
            </View>
            <ScrollView style={styles.messagesContainer} contentContainerStyle={styles.messagesContent}>
              {chatMessages.length === 0 ? (
                <View style={styles.welcomeMessage}>
                  <View style={styles.welcomeIconContainer}>
                    <Ionicons name="sparkles" size={48} color="#007AFF" />
                  </View>
                  <Text style={styles.welcomeTitle}>Hey {user.name}! I'm Maya, your AI stylist 👗</Text>
                  <Text style={styles.welcomeText}>Ready for a fresh styling session? I'm here to help you look amazing! Ask me anything about fashion.</Text>
                  <View style={styles.welcomeHints}>
                    <View style={styles.hintRow}>
                      <Ionicons name="chatbubble-outline" size={16} color="#007AFF" />
                      <Text style={styles.hintText}>"What should I wear to work today?"</Text>
                    </View>
                    <View style={styles.hintRow}>
                      <Ionicons name="camera-outline" size={16} color="#007AFF" />
                      <Text style={styles.hintText}>Upload a photo for styling advice</Text>
                    </View>
                    <View style={styles.hintRow}>
                      <Ionicons name="shirt-outline" size={16} color="#007AFF" />
                      <Text style={styles.hintText}>"Mix and match ideas from my wardrobe"</Text>
                    </View>
                  </View>
                </View>
              ) : (
                chatMessages.map((msg) => (
                  <View
                    key={msg.id}
                    style={[styles.message, msg.is_user ? styles.userMessage : styles.aiMessage]}
                  >
                    {msg.image_base64 && (
                      <Image
                        source={{ uri: msg.image_base64.startsWith('data:') ? msg.image_base64 : `data:image/jpeg;base64,${msg.image_base64}` }}
                        style={styles.messageImage}
                        resizeMode="contain"
                        onError={() => console.log('Image failed to load')}
                      />
                    )}
                    {msg.isTyping ? (
                      <View style={styles.typingIndicator}>
                        <View style={styles.typingDot} />
                        <View style={[styles.typingDot, { marginLeft: 4 }]} />
                        <View style={[styles.typingDot, { marginLeft: 4 }]} />
                      </View>
                    ) : (
                      <Text style={[styles.messageText, msg.is_user ? styles.userMessageText : styles.aiMessageText]}>
                        {msg.message}
                      </Text>
                    )}
                  </View>
                ))
              )}
            </ScrollView>
            
            {chatImage && (
              <View style={styles.imagePreview}>
                <Image
                  source={{ uri: `data:image/jpeg;base64,${chatImage}` }}
                  style={styles.previewImage}
                  onError={(error) => {
                    console.error('Image display error:', error);
                    setChatImage(null);
                  }}
                />
                <TouchableOpacity
                  style={styles.removeImageButton}
                  onPress={() => setChatImage(null)}
                >
                  <Ionicons name="close" size={20} color="white" />
                </TouchableOpacity>
              </View>
            )}
            
            <View style={styles.inputContainer}>
              <TextInput
                style={styles.messageInput}
                placeholder="Ask Maya for styling advice..."
                value={chatInput}
                onChangeText={setChatInput}
                multiline
                maxLength={500}
              />
              <TouchableOpacity
                style={styles.photoButton}
                onPress={selectChatImage}
                disabled={loading}
              >
                <Ionicons name="camera" size={24} color="#007AFF" />
              </TouchableOpacity>
              <TouchableOpacity
                style={[styles.sendButton, (loading || (!chatInput.trim() && !chatImage)) && styles.disabledButton]}
                onPress={sendMessage}
                disabled={loading || (!chatInput.trim() && !chatImage)}
              >
                {loading ? (
                  <ActivityIndicator size="small" color="white" />
                ) : (
                  <Ionicons name="send" size={20} color="white" />
                )}
              </TouchableOpacity>
            </View>
          </KeyboardAvoidingView>
        )}

        {currentTab === 'wardrobe' && (
          <View style={styles.wardrobeContainer}>
            <View style={styles.wardrobeHeader}>
              <Text style={styles.wardrobeTitle}>My Wardrobe</Text>
              <TouchableOpacity
                style={styles.addButton}
                onPress={addWardrobeItems}
                disabled={loading}
              >
                {loading ? (
                  <ActivityIndicator size="small" color="white" />
                ) : (
                  <Ionicons name="add" size={24} color="white" />
                )}
              </TouchableOpacity>
            </View>

            {/* Upload Progress Removed as requested */}

            {/* Category Filters */}
            {wardrobe.length > 0 && (
              <ScrollView 
                horizontal 
                showsHorizontalScrollIndicator={false} 
                style={styles.categoryFiltersContainer}
                contentContainerStyle={styles.categoryFiltersContent}
              >
                <TouchableOpacity
                  style={[
                    styles.categoryFilter,
                    selectedCategoryFilter === 'all' && styles.activeFilter
                  ]}
                  onPress={() => setSelectedCategoryFilter('all')}
                >
                  <Text style={[
                    styles.filterText,
                    selectedCategoryFilter === 'all' && styles.activeFilterText
                  ]}>
                    All ({wardrobe.length})
                  </Text>
                </TouchableOpacity>
                
                {getAvailableCategories().map(category => {
                  const count = wardrobe.filter(item => (item.category || 'Other') === category).length;
                  return (
                    <TouchableOpacity
                      key={category}
                      style={[
                        styles.categoryFilter,
                        selectedCategoryFilter === category && styles.activeFilter
                      ]}
                      onPress={() => setSelectedCategoryFilter(category)}
                    >
                      <Text style={[
                        styles.filterText,
                        selectedCategoryFilter === category && styles.activeFilterText
                      ]}>
                        {category.charAt(0).toUpperCase() + category.slice(1)} ({count})
                      </Text>
                    </TouchableOpacity>
                  );
                })}
              </ScrollView>
            )}
            
            <ScrollView contentContainerStyle={styles.wardrobeGrid}>
              {wardrobe.length === 0 && !loading ? (
                <View style={styles.emptyWardrobe}>
                  <View style={styles.emptyIconContainer}>
                    <Ionicons name="shirt-outline" size={64} color="#007AFF" />
                  </View>
                  <Text style={styles.emptyTitle}>Build Your Digital Wardrobe</Text>
                  <Text style={styles.emptyText}>Upload photos of your clothes and let AI help organize and style them</Text>
                  <View style={styles.emptyFeatures}>
                    <View style={styles.featureRow}>
                      <Ionicons name="camera-outline" size={20} color="#007AFF" />
                      <Text style={styles.featureText}>Multiple photo upload</Text>
                    </View>
                    <View style={styles.featureRow}>
                      <Ionicons name="color-palette-outline" size={20} color="#007AFF" />
                      <Text style={styles.featureText}>AI identifies details & fabrics</Text>
                    </View>
                    <View style={styles.featureRow}>
                      <Ionicons name="sparkles-outline" size={20} color="#007AFF" />
                      <Text style={styles.featureText}>Get personalized styling</Text>
                    </View>
                  </View>
                  <TouchableOpacity
                    style={styles.getStartedButton}
                    onPress={addWardrobeItems}
                    disabled={loading}
                  >
                    <Ionicons name="add-circle-outline" size={24} color="white" />
                    <Text style={styles.getStartedText}>{loading ? 'Adding...' : 'Add Your First Items'}</Text>
                  </TouchableOpacity>
                </View>
              ) : (
                <View style={styles.categorizedWardrobe}>
                  {Object.entries(getFilteredWardrobe()).map(([category, items]) => (
                    <View key={category} style={styles.categorySection}>
                      <Text style={styles.categoryHeader}>{category.charAt(0).toUpperCase() + category.slice(1)}</Text>
                      <View style={styles.itemsGrid}>
                        {items.map((item) => (
                          <View key={item.id} style={styles.wardrobeItem}>
                            <Image
                              source={{ uri: `data:image/jpeg;base64,${item.image_base64}` }}
                              style={styles.itemImage}
                              resizeMode="cover"
                              onError={(error) => {
                                console.error('Wardrobe item image display error:', error);
                              }}
                            />
                            <TouchableOpacity
                              style={styles.deleteButton}
                              onPress={() => deleteWardrobeItem(item.id)}
                            >
                              <Ionicons name="trash-outline" size={16} color="white" />
                            </TouchableOpacity>
                            <View style={styles.itemInfo}>
                              <Text style={styles.itemName}>
                                {item.exact_item_name || item.category || 'Item'}
                              </Text>
                              <Text style={styles.itemDetails}>
                                {item.color} • {item.fabric_type || item.style || 'Style'}
                              </Text>
                              {item.tags.length > 0 && (
                                <Text style={styles.itemTags}>{item.tags.slice(0, 2).join(', ')}</Text>
                              )}
                            </View>
                          </View>
                        ))}
                      </View>
                    </View>
                  ))}
                </View>
              )}
            </ScrollView>
          </View>
        )}

        {currentTab === 'validate' && (
          <ScrollView style={styles.validateContainer}>
            <View style={styles.validateHeader}>
              <Text style={styles.validateTitle}>Validate Your Outfit</Text>
              <Text style={styles.validateSubtitle}>Get Maya's expert styling feedback</Text>
            </View>
            
            <TouchableOpacity
              style={styles.uploadOutfitButton}
              onPress={validateOutfit}
              disabled={loading}
            >
              <Ionicons name="camera-outline" size={48} color="#007AFF" />
              <Text style={styles.uploadOutfitText}>
                {loading ? 'Analyzing...' : 'Upload Your Outfit Photo'}
              </Text>
              <Text style={styles.uploadOutfitHint}>Take a mirror selfie or full-body photo</Text>
            </TouchableOpacity>
            
            {lastValidation && (
              <ScrollView style={styles.validationResult}>
                {/* Display user's outfit image */}
                <View style={styles.uploadedImageContainer}>
                  {lastValidation.image_base64 ? (
                    <Image
                      source={{ uri: `data:image/jpeg;base64,${lastValidation.image_base64.replace(/^data:image\/[a-z]+;base64,/, '')}` }}
                      style={styles.uploadedOutfitImage}
                      resizeMode="contain"
                      onError={(error) => {
                        console.error('Validation image display error:', error);
                        setLastValidation(null);
                      }}
                    />
                  ) : (
                    <View style={[styles.uploadedOutfitImage, { backgroundColor: '#f0f0f0', justifyContent: 'center', alignItems: 'center' }]}>
                      <Text style={{ color: '#666' }}>Image not available</Text>
                    </View>
                  )}
                </View>

                <View style={styles.verdictContainer}>
                  <Text style={styles.validationTitle}>Maya's Fashion Verdict</Text>
                  
                  {/* Overall Score Circle */}
                  <View style={styles.overallScoreContainer}>
                    <View style={[styles.scoreCircle, { 
                      borderColor: lastValidation.overall_score >= 4 ? '#22C55E' : 
                                   lastValidation.overall_score >= 3 ? '#F59E0B' : '#EF4444'
                    }]}>
                      <Text style={styles.overallScoreText}>
                        {Math.round((lastValidation.overall_score / 5) * 100)}%
                      </Text>
                    </View>
                    <Text style={styles.overallLabel}>Style Score</Text>
                  </View>

                  {/* Detailed Metrics */}
                  <View style={styles.metricsContainer}>
                    <View style={styles.metricRow}>
                      <View style={styles.metricHeader}>
                        <Ionicons name="color-palette-outline" size={24} color="#3B82F6" />
                        <Text style={styles.metricLabel}>Color Match</Text>
                      </View>
                      <View style={styles.metricScore}>
                        <View style={[styles.scoreBar, { width: `${(lastValidation.scores.color_combo / 5) * 100}%` }]} />
                        <Text style={styles.scoreValue}>{lastValidation.scores.color_combo}/5</Text>
                      </View>
                    </View>

                    <View style={styles.metricRow}>
                      <View style={styles.metricHeader}>
                        <Ionicons name="shirt-outline" size={24} color="#8B5CF6" />
                        <Text style={styles.metricLabel}>Style Fit</Text>
                      </View>
                      <View style={styles.metricScore}>
                        <View style={[styles.scoreBar, { width: `${(lastValidation.scores.fit / 5) * 100}%` }]} />
                        <Text style={styles.scoreValue}>{lastValidation.scores.fit}/5</Text>
                      </View>
                    </View>

                    <View style={styles.metricRow}>
                      <View style={styles.metricHeader}>
                        <Ionicons name="calendar-outline" size={24} color="#F59E0B" />
                        <Text style={styles.metricLabel}>Occasion</Text>
                      </View>
                      <View style={styles.metricScore}>
                        <View style={[styles.scoreBar, { width: `${(lastValidation.scores.occasion / 5) * 100}%` }]} />
                        <Text style={styles.scoreValue}>{lastValidation.scores.occasion}/5</Text>
                      </View>
                    </View>

                    <View style={styles.metricRow}>
                      <View style={styles.metricHeader}>
                        <Ionicons name="diamond-outline" size={24} color="#EF4444" />
                        <Text style={styles.metricLabel}>Coordination</Text>
                      </View>
                      <View style={styles.metricScore}>
                        <View style={[styles.scoreBar, { width: `${(lastValidation.scores.style / 5) * 100}%` }]} />
                        <Text style={styles.scoreValue}>{lastValidation.scores.style}/5</Text>
                      </View>
                    </View>
                  </View>

                  {/* Professional Feedback */}
                  <View style={styles.feedbackContainer}>
                    <Text style={styles.feedbackTitle}>Maya's Styling Notes</Text>
                    <Text style={styles.professionalFeedback}>{lastValidation.feedback}</Text>
                  </View>
                </View>
              </ScrollView>
            )}
          </ScrollView>
        )}

        {currentTab === 'profile' && (
          <ScrollView style={styles.profileContainer}>
            <View style={styles.profileHeader}>
              <View style={styles.profileAvatar}>
                <Ionicons name="person" size={48} color="#007AFF" />
              </View>
              <Text style={styles.profileName}>{user.name}</Text>
              <Text style={styles.profileEmail}>{user.email}</Text>
            </View>
            
            <View style={styles.profileSection}>
              <Text style={styles.sectionTitle}>Style Profile</Text>
              
              <View style={styles.profileRow}>
                <Ionicons name="location-outline" size={20} color="#666" />
                <Text style={styles.profileLabel}>City</Text>
                <Text style={styles.profileValue}>{user.city || 'Not specified'}</Text>
              </View>
              
              <View style={styles.profileRow}>
                <Ionicons name="person-outline" size={20} color="#666" />
                <Text style={styles.profileLabel}>Age</Text>
                <Text style={styles.profileValue}>{user.age || 'Not specified'}</Text>
              </View>
              
              <View style={styles.profileRow}>
                <Ionicons name="briefcase-outline" size={20} color="#666" />
                <Text style={styles.profileLabel}>Profession</Text>
                <Text style={styles.profileValue}>{user.profession || 'Not specified'}</Text>
              </View>
              
              <View style={styles.profileRow}>
                <Ionicons name="color-palette-outline" size={20} color="#666" />
                <Text style={styles.profileLabel}>Style Vibes</Text>
                <Text style={styles.profileValue}>{user.style_vibes?.join(', ') || 'Not specified'}</Text>
              </View>
            </View>
            
            <View style={styles.profileSection}>
              <Text style={styles.sectionTitle}>Statistics</Text>
              
              <View style={styles.statsGrid}>
                <View style={styles.statCard}>
                  <Text style={styles.statNumber}>{wardrobe.length}</Text>
                  <Text style={styles.statLabel}>Wardrobe Items</Text>
                </View>
                
                <View style={styles.statCard}>
                  <Text style={styles.statNumber}>{Math.floor(chatMessages.length / 2)}</Text>
                  <Text style={styles.statLabel}>Style Conversations</Text>
                </View>
              </View>
            </View>
            
            {user.onboarding_completed && (
              <TouchableOpacity
                style={styles.editProfileButton}
                onPress={() => setShowOnboarding(true)}
              >
                <Ionicons name="create-outline" size={20} color="#007AFF" />
                <Text style={styles.editProfileText}>Edit Style Profile</Text>
              </TouchableOpacity>
            )}
          </ScrollView>
        )}
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f8f9fa',
  },
  // Auth styles
  authContainer: {
    flex: 1,
    backgroundColor: '#f8f9fa',
  },
  authKeyboard: {
    flex: 1,
  },
  authScrollView: {
    flexGrow: 1,
    justifyContent: 'center',
    padding: 24,
  },
  authHeader: {
    alignItems: 'center',
    marginBottom: 48,
  },
  authForm: {
    width: '100%',
    maxWidth: 400,
    alignSelf: 'center',
  },
  input: {
    borderWidth: 1,
    borderColor: '#e1e5e9',
    borderRadius: 12,
    padding: 16,
    fontSize: 16,
    backgroundColor: '#fff',
    marginBottom: 16,
  },
  authButton: {
    backgroundColor: '#007AFF',
    padding: 16,
    borderRadius: 12,
    alignItems: 'center',
    marginBottom: 16,
  },
  disabledButton: {
    opacity: 0.6,
  },
  authButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },
  switchAuthButton: {
    alignItems: 'center',
    padding: 8,
  },
  switchAuthText: {
    color: '#007AFF',
    fontSize: 14,
  },
  debugContainer: {
    backgroundColor: '#fff3cd',
    borderColor: '#ffeaa7',
    borderWidth: 1,
    borderRadius: 8,
    padding: 12,
    marginBottom: 16,
  },
  debugText: {
    color: '#856404',
    fontSize: 12,
    fontFamily: 'monospace',
  },
  logoContainer: {
    width: 80,
    height: 80,
    borderRadius: 40,
    backgroundColor: '#f0f8ff',
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 24,
  },
  appTitle: {
    fontSize: 32,
    fontWeight: 'bold',
    color: '#007AFF',
    marginBottom: 8,
  },
  appSubtitle: {
    fontSize: 16,
    color: '#666',
    textAlign: 'center',
    marginBottom: 8,
  },
  appTagline: {
    fontSize: 14,
    color: '#888',
    textAlign: 'center',
    fontStyle: 'italic',
    paddingHorizontal: 20,
  },
  authToggle: {
    flexDirection: 'row',
    backgroundColor: '#e9ecef',
    borderRadius: 8,
    padding: 4,
    marginBottom: 32,
  },
  toggleButton: {
    flex: 1,
    padding: 12,
    alignItems: 'center',
    borderRadius: 6,
  },
  activeToggle: {
    backgroundColor: 'white',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.1,
    shadowRadius: 2,
    elevation: 2,
  },
  toggleText: {
    fontSize: 16,
    color: '#666',
  },
  activeToggleText: {
    color: '#007AFF',
    fontWeight: '600',
  },
  form: {
    gap: 16,
  },
  input: {
    borderWidth: 1,
    borderColor: '#ddd',
    borderRadius: 8,
    padding: 16,
    fontSize: 16,
    backgroundColor: 'white',
  },
  languageSelector: {
    gap: 12,
  },
  languageLabel: {
    fontSize: 16,
    color: '#333',
    fontWeight: '500',
  },
  languageButtons: {
    flexDirection: 'row',
    gap: 8,
  },
  langButton: {
    flex: 1,
    padding: 12,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#ddd',
    alignItems: 'center',
    backgroundColor: 'white',
  },
  activeLang: {
    borderColor: '#007AFF',
    backgroundColor: '#f0f8ff',
  },
  langText: {
    fontSize: 16,
    color: '#666',
  },
  activeLangText: {
    color: '#007AFF',
    fontWeight: '600',
  },
  authButton: {
    backgroundColor: '#007AFF',
    padding: 16,
    borderRadius: 8,
    alignItems: 'center',
    marginTop: 8,
  },
  disabledButton: {
    opacity: 0.6,
  },
  authButtonText: {
    color: 'white',
    fontSize: 18,
    fontWeight: '600',
  },

  // Enhanced onboarding styles with visual cards
  onboardingContainer: {
    flexGrow: 1,
    padding: 24,
  },
  onboardingHeader: {
    alignItems: 'center',
    marginBottom: 32,
  },
  onboardingTitle: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#333',
    textAlign: 'center',
    marginBottom: 8,
  },
  onboardingSubtitle: {
    fontSize: 16,
    color: '#666',
    marginBottom: 16,
  },
  progressBar: {
    width: '100%',
    height: 4,
    backgroundColor: '#e9ecef',
    borderRadius: 2,
    overflow: 'hidden',
  },
  progressFill: {
    height: '100%',
    backgroundColor: '#007AFF',
    borderRadius: 2,
  },
  onboardingStep: {
    flex: 1,
    gap: 16,
  },
  stepTitle: {
    fontSize: 22,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 8,
    textAlign: 'center',
  },
  stepSubtitle: {
    fontSize: 16,
    color: '#666',
    marginBottom: 24,
    textAlign: 'center',
  },
  
  // Visual card styles
  cardGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 16,
    justifyContent: 'space-between',
  },
  visualCard: {
    width: '47%',
    padding: 20,
    borderRadius: 16,
    borderWidth: 2,
    borderColor: '#e9ecef',
    backgroundColor: 'white',
    alignItems: 'center',
    minHeight: 120,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 2,
  },
  selectedCard: {
    borderColor: '#007AFF',
    backgroundColor: '#f0f8ff',
    transform: [{ scale: 1.02 }],
  },
  cardIcon: {
    width: 60,
    height: 60,
    borderRadius: 30,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 12,
  },
  cardLabel: {
    fontSize: 16,
    fontWeight: '600',
    color: '#333',
    textAlign: 'center',
    marginBottom: 4,
  },
  cardSubtitle: {
    fontSize: 12,
    color: '#666',
    textAlign: 'center',
  },
  bodyShapeIcon: {
    fontSize: 48,
    marginBottom: 12,
  },
  
  // Skin tone selection
  skinToneGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 12,
    justifyContent: 'center',
  },
  skinToneCard: {
    width: 80,
    height: 80,
    borderRadius: 40,
    alignItems: 'center',
    justifyContent: 'center',
    borderWidth: 3,
    borderColor: 'transparent',
  },
  selectedSkinTone: {
    borderColor: '#007AFF',
    transform: [{ scale: 1.1 }],
  },
  skinToneLabel: {
    fontSize: 10,
    fontWeight: '600',

  // Body shape with images
  bodyShapeCard: {
    width: '47%',
    padding: 16,
    borderRadius: 16,
    borderWidth: 2,
    borderColor: '#e9ecef',
    backgroundColor: 'white',
    alignItems: 'center',
    minHeight: 180,
  },
  bodyShapeImage: {
    width: 80,
    height: 120,
    marginBottom: 12,
  },
  
  // Style Inspiration
  styleInspirationGrid: {
    gap: 16,
  },
  styleInspirationCard: {
    width: '100%',
    borderRadius: 16,
    borderWidth: 2,
    borderColor: '#e9ecef',
    backgroundColor: 'white',
    overflow: 'hidden',
    marginBottom: 16,
  },
  selectedStyleCard: {
    borderColor: '#007AFF',
    borderWidth: 3,
  },
  styleInspirationImage: {
    width: '100%',
    height: 200,
  },
  styleInspirationTextContainer: {
    padding: 16,
  },
  styleInspirationLabel: {
    fontSize: 18,
    fontWeight: '600',
    color: '#333',
    marginBottom: 4,
  },
  styleInspirationDescription: {
    fontSize: 14,
    color: '#666',
  },
  
  // Style Vibe
  styleVibeScroll: {
    flex: 1,
  },
  styleVibeCard: {
    width: '100%',
    borderRadius: 16,
    borderWidth: 2,
    borderColor: '#e9ecef',
    backgroundColor: 'white',
    overflow: 'hidden',
    marginBottom: 16,
    position: 'relative',
  },
  selectedStyleVibeCard: {
    borderColor: '#007AFF',
    borderWidth: 3,
  },
  styleVibeImage: {
    width: '100%',
    height: 240,
  },
  styleVibeTextContainer: {
    padding: 16,
  },
  styleVibeLabel: {
    fontSize: 18,
    fontWeight: '600',
    color: '#333',
    marginBottom: 4,
  },
  styleVibeDescription: {
    fontSize: 14,
    color: '#666',
  },
  styleVibeCheckmark: {
    position: 'absolute',
    top: 12,
    right: 12,
    backgroundColor: 'white',
    borderRadius: 14,
  },
  
  // Style Message
  styleMessageGrid: {
    gap: 12,
  },
  styleMessageCard: {
    width: '100%',
    padding: 20,
    borderRadius: 16,
    borderWidth: 2,
    borderColor: '#e9ecef',
    backgroundColor: 'white',
    flexDirection: 'row',
    alignItems: 'center',
  },
  selectedStyleMessageCard: {
    borderColor: '#007AFF',
    borderWidth: 3,
    backgroundColor: '#f0f8ff',
  },
  styleMessageLabel: {
    fontSize: 16,
    fontWeight: '600',
    color: '#333',
    flex: 1,
    marginLeft: 12,
  },

    textAlign: 'center',
    color: '#333',
    textShadowColor: 'rgba(255, 255, 255, 0.8)',
    textShadowOffset: { width: 1, height: 1 },
    textShadowRadius: 2,
  },
  
  onboardingButtons: {
    flexDirection: 'row',
    gap: 16,
    marginTop: 32,
    alignItems: 'center',
  },
  backButton: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 16,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#007AFF',
    gap: 8,
  },
  backButtonText: {
    color: '#007AFF',
    fontSize: 16,
    fontWeight: '600',
  },
  nextButton: {
    flex: 2,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#007AFF',
    padding: 16,
    borderRadius: 8,
    gap: 8,
  },
  nextButtonText: {
    color: 'white',
    fontSize: 16,
    fontWeight: '600',
  },

  // Main app styles
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 16,
    backgroundColor: 'white',
    borderBottomWidth: 1,
    borderBottomColor: '#e9ecef',
  },
  headerTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#333',
  },
  logoutButton: {
    padding: 8,
  },
  tabBar: {
    flexDirection: 'row',
    backgroundColor: 'white',
    borderBottomWidth: 1,
    borderBottomColor: '#e9ecef',
  },
  tab: {
    flex: 1,
    alignItems: 'center',
    paddingVertical: 12,
    gap: 4,
  },
  activeTab: {
    borderBottomWidth: 2,
    borderBottomColor: '#007AFF',
  },
  tabText: {
    fontSize: 12,
    color: '#666',
  },
  activeTabText: {
    color: '#007AFF',
    fontWeight: '600',
  },
  content: {
    flex: 1,
  },

  // Fresh chat styles
  chatContainer: {
    flex: 1,
  },
  messagesContainer: {
    flex: 1,
  },
  messagesContent: {
    padding: 16,
    paddingBottom: 8,
  },
  welcomeMessage: {
    alignItems: 'center',
    paddingTop: 64,
    paddingHorizontal: 24,
  },
  welcomeIconContainer: {
    width: 80,
    height: 80,
    borderRadius: 40,
    backgroundColor: '#f0f8ff',
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 24,
  },
  welcomeTitle: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 8,
    textAlign: 'center',
  },
  welcomeText: {
    fontSize: 16,
    color: '#666',
    textAlign: 'center',
    lineHeight: 24,
    marginBottom: 32,
  },
  welcomeHints: {
    alignSelf: 'stretch',
    gap: 16,
  },
  hintRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    paddingHorizontal: 16,
  },
  hintText: {
    fontSize: 14,
    color: '#666',
    flex: 1,
  },
  message: {
    marginBottom: 16,
    maxWidth: '80%',
  },
  userMessage: {
    alignSelf: 'flex-end',
    backgroundColor: '#007AFF',
    borderRadius: 18,
    padding: 12,
  },
  aiMessage: {
    alignSelf: 'flex-start',
    backgroundColor: 'white',
    borderRadius: 18,
    padding: 12,
    borderWidth: 1,
    borderColor: '#e9ecef',
  },
  messageText: {
    fontSize: 16,
    lineHeight: 22,
  },
  userMessageText: {
    color: 'white',
  },
  aiMessageText: {
    color: '#333',
  },
  typingIndicator: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 8,
  },
  typingDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    backgroundColor: '#666',
    opacity: 0.7,
  },
  messageImage: {
    width: 200,
    height: 200,
    borderRadius: 12,
    marginBottom: 8,
  },
  imagePreview: {
    margin: 16,
    position: 'relative',
    alignSelf: 'center',
  },
  previewImage: {
    width: 120,
    height: 120,
    borderRadius: 8,
  },
  removeImageButton: {
    position: 'absolute',
    top: -8,
    right: -8,
    width: 24,
    height: 24,
    borderRadius: 12,
    backgroundColor: 'red',
    alignItems: 'center',
    justifyContent: 'center',
  },
  inputContainer: {
    flexDirection: 'row',
    padding: 16,
    backgroundColor: 'white',
    borderTopWidth: 1,
    borderTopColor: '#e9ecef',
    alignItems: 'flex-end',
    gap: 8,
  },
  messageInput: {
    flex: 1,
    borderWidth: 1,
    borderColor: '#ddd',
    borderRadius: 20,
    paddingHorizontal: 16,
    paddingVertical: 12,
    fontSize: 16,
    maxHeight: 100,
  },
  photoButton: {
    width: 44,
    height: 44,
    borderRadius: 22,
    backgroundColor: '#f0f8ff',
    alignItems: 'center',
    justifyContent: 'center',
  },
  sendButton: {
    width: 44,
    height: 44,
    borderRadius: 22,
    backgroundColor: '#007AFF',
    alignItems: 'center',
    justifyContent: 'center',
  },

  // Enhanced wardrobe styles
  wardrobeContainer: {
    flex: 1,
  },
  wardrobeHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 16,
    backgroundColor: 'white',
    borderBottomWidth: 1,
    borderBottomColor: '#e9ecef',
  },
  wardrobeTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#333',
  },
  addButton: {
    width: 44,
    height: 44,
    borderRadius: 22,
    backgroundColor: '#007AFF',
    alignItems: 'center',
    justifyContent: 'center',
  },
  wardrobeGrid: {
    padding: 16,
  },
  emptyWardrobe: {
    alignItems: 'center',
    paddingTop: 64,
    paddingHorizontal: 24,
  },
  emptyIconContainer: {
    width: 100,
    height: 100,
    borderRadius: 50,
    backgroundColor: '#f0f8ff',
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 24,
  },
  emptyTitle: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 8,
  },
  emptyText: {
    fontSize: 16,
    color: '#666',
    textAlign: 'center',
    lineHeight: 24,
    marginBottom: 32,
  },
  emptyFeatures: {
    alignSelf: 'stretch',
    gap: 16,
    marginBottom: 32,
  },
  featureRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    paddingHorizontal: 16,
  },
  featureText: {
    fontSize: 14,
    color: '#666',
    flex: 1,
  },
  getStartedButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#007AFF',
    paddingVertical: 16,
    paddingHorizontal: 24,
    borderRadius: 12,
    gap: 8,
  },
  getStartedText: {
    color: 'white',
    fontSize: 16,
    fontWeight: '600',
  },
  itemsGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 16,
  },
  wardrobeItem: {
    width: '47%',
    backgroundColor: 'white',
    borderRadius: 12,
    overflow: 'hidden',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  itemImage: {
    width: '100%',
    height: 160,
    borderTopLeftRadius: 12,
    borderTopRightRadius: 12,
  },
  itemInfo: {
    padding: 12,
    gap: 4,
  },
  itemName: {
    fontSize: 16,
    fontWeight: '600',
    color: '#333',
  },
  itemDetails: {
    fontSize: 14,
    color: '#666',
  },
  itemTags: {
    fontSize: 12,
    color: '#999',
  },
  categorizedWardrobe: {
    gap: 24,
  },
  categorySection: {
    gap: 12,
  },
  categoryHeader: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 8,
    paddingHorizontal: 4,
  },
  deleteButton: {
    position: 'absolute',
    top: 8,
    right: 8,
    width: 28,
    height: 28,
    borderRadius: 14,
    backgroundColor: 'rgba(255, 0, 0, 0.8)',
    alignItems: 'center',
    justifyContent: 'center',
    zIndex: 1,
  },
  chatHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 16,
    backgroundColor: 'white',
    borderBottomWidth: 1,
    borderBottomColor: '#e9ecef',
  },
  chatHeaderTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#333',
  },
  newChatButton: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderRadius: 20,
    backgroundColor: '#f0f8ff',
    gap: 4,
  },
  newChatText: {
    fontSize: 14,
    color: '#007AFF',
    fontWeight: '600',
  },

  // Enhanced validate styles
  validateContainer: {
    flex: 1,
  },
  validateHeader: {
    alignItems: 'center',
    padding: 24,
    backgroundColor: 'white',
    borderBottomWidth: 1,
    borderBottomColor: '#e9ecef',
  },
  validateTitle: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 4,
  },
  validateSubtitle: {
    fontSize: 16,
    color: '#666',
  },
  uploadOutfitButton: {
    margin: 16,
    padding: 32,
    borderRadius: 16,
    borderWidth: 2,
    borderColor: '#007AFF',
    borderStyle: 'dashed',
    alignItems: 'center',
    backgroundColor: '#f0f8ff',
  },
  uploadOutfitText: {
    fontSize: 18,
    fontWeight: '600',
    color: '#007AFF',
    marginTop: 16,
    marginBottom: 8,
  },
  uploadOutfitHint: {
    fontSize: 14,
    color: '#666',
  },
  validationResult: {
    flex: 1,
    margin: 16,
  },
  uploadedImageContainer: {
    alignItems: 'center',
    marginBottom: 24,
    padding: 20,
    backgroundColor: 'white',
    borderRadius: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 16,
    textAlign: 'center',
  },
  uploadedOutfitImage: {
    width: 200,
    height: 250,
    borderRadius: 12,
    backgroundColor: '#f8f9fa',
  },
  verdictContainer: {
    padding: 20,
    backgroundColor: 'white',
    borderRadius: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  validationTitle: {
    fontSize: 22,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 24,
    textAlign: 'center',
  },
  overallScoreContainer: {
    alignItems: 'center',
    marginBottom: 32,
  },
  scoreCircle: {
    width: 120,
    height: 120,
    borderRadius: 60,
    borderWidth: 8,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#ffffff',
    marginBottom: 12,
  },
  overallScoreText: {
    fontSize: 32,
    fontWeight: 'bold',
    color: '#333',
  },
  overallLabel: {
    fontSize: 16,
    color: '#666',
    textAlign: 'center',
  },
  metricsContainer: {
    gap: 20,
    marginBottom: 24,
  },
  metricRow: {
    gap: 12,
  },
  metricHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    marginBottom: 8,
  },
  metricLabel: {
    fontSize: 16,
    fontWeight: '600',
    color: '#333',
    flex: 1,
  },
  metricScore: {
    position: 'relative',
    height: 8,
    backgroundColor: '#e5e7eb',
    borderRadius: 4,
    overflow: 'hidden',
    marginBottom: 4,
  },
  scoreBar: {
    height: '100%',
    backgroundColor: '#3B82F6',
    borderRadius: 4,
  },
  scoreValue: {
    fontSize: 14,
    fontWeight: '600',
    color: '#666',
    textAlign: 'right',
    marginTop: 4,
  },
  feedbackContainer: {
    backgroundColor: '#f8f9fa',
    padding: 20,
    borderRadius: 12,
    borderLeftWidth: 4,
    borderLeftColor: '#3B82F6',
  },
  feedbackTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 12,
  },
  professionalFeedback: {
    fontSize: 16,
    color: '#555',
    lineHeight: 24,
    fontStyle: 'normal',
  },

  // Profile styles
  profileContainer: {
    flex: 1,
  },
  profileHeader: {
    alignItems: 'center',
    padding: 24,
    backgroundColor: 'white',
    borderBottomWidth: 1,
    borderBottomColor: '#e9ecef',
  },
  profileAvatar: {
    width: 80,
    height: 80,
    borderRadius: 40,
    backgroundColor: '#f0f8ff',
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 16,
  },
  profileName: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 4,
  },
  profileEmail: {
    fontSize: 16,
    color: '#666',
  },
  profileSection: {
    backgroundColor: 'white',
    marginTop: 16,
    padding: 16,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 16,
  },
  profileRow: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#f0f0f0',
    gap: 12,
  },
  profileLabel: {
    flex: 1,
    fontSize: 16,
    color: '#333',
  },
  profileValue: {
    fontSize: 16,
    color: '#666',
  },
  statsGrid: {
    flexDirection: 'row',
    gap: 16,
  },
  statCard: {
    flex: 1,
    backgroundColor: '#f8f9fa',
    padding: 20,
    borderRadius: 12,
    alignItems: 'center',
  },
  statNumber: {
    fontSize: 32,
    fontWeight: 'bold',
    color: '#007AFF',
    marginBottom: 4,
  },
  statLabel: {
    fontSize: 14,
    color: '#666',
    textAlign: 'center',
  },
  editProfileButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    margin: 16,
    padding: 16,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: '#007AFF',
    gap: 8,
  },
  editProfileText: {
    fontSize: 16,
    color: '#007AFF',
    fontWeight: '600',
  },
});
