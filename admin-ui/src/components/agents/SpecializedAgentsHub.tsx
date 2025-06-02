import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { 
  User, 
  Home, 
  Heart, 
  Search, 
  TrendingUp, 
  MapPin, 
  Activity,
  Brain,
  Loader2,
  CheckCircle,
  XCircle
} from 'lucide-react';

interface AgentStatus {
  id: string;
  name: string;
  type: string;
  status: string;
  created_at: string;
  last_activity: string;
  tasks_completed: number;
}

interface SearchResult {
  query: string;
  results: Array<{
    id: string;
    content: string;
    final_score: number;
  }>;
  preferences_applied: string[];
  search_id: string;
}

interface ApartmentListing {
  id: string;
  address: string;
  price: number;
  bedrooms: number;
  bathrooms: number;
  sqft: number;
  tech_score: number;
  neighborhood_score: number;
  overall_score: number;
}

interface ClinicalTrial {
  nct_id: string;
  title: string;
  phase: string;
  conditions: string[];
  relevance_score: number;
  distance_miles?: number;
}

export const SpecializedAgentsHub: React.FC = () => {
  const [agents, setAgents] = useState<Record<string, AgentStatus>>({});
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  // Personal Agent State
  const [personalQuery, setPersonalQuery] = useState('');
  const [personalUserId, setPersonalUserId] = useState('user123');
  const [personalResults, setPersonalResults] = useState<SearchResult | null>(null);
  
  // Pay Ready Agent State
  const [apartmentData, setApartmentData] = useState({
    id: '',
    address: '',
    price: '',
    bedrooms: '',
    bathrooms: '',
    sqft: '',
    amenities: '',
    smart_home_features: ''
  });
  const [apartmentResult, setApartmentResult] = useState<any>(null);
  
  // Paragon Medical Agent State
  const [medicalConditions, setMedicalConditions] = useState('');
  const [medicalPhases, setMedicalPhases] = useState('Phase 3, Phase 4');
  const [medicalResults, setMedicalResults] = useState<any>(null);

  useEffect(() => {
    fetchAgentStatus();
    const interval = setInterval(fetchAgentStatus, 10000); // Refresh every 10s
    return () => clearInterval(interval);
  }, []);

  const fetchAgentStatus = async () => {
    try {
      const response = await fetch('/api/orchestration/agents');
      if (!response.ok) throw new Error('Failed to fetch agents');
      const data = await response.json();
      setAgents(data.agents);
    } catch (err) {
      console.error('Error fetching agents:', err);
    }
  };

  // Personal Agent Functions
  const executePersonalSearch = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch('/api/orchestration/personal/search', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_id: personalUserId,
          query: personalQuery,
          search_type: 'comprehensive'
        })
      });
      
      if (!response.ok) throw new Error('Search failed');
      const result = await response.json();
      setPersonalResults(result);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const learnPreference = async (category: string, signal: 'positive' | 'negative') => {
    try {
      const response = await fetch(`/api/orchestration/personal/learn-preference?user_id=${personalUserId}&category=${category}&signal_type=${signal}`, {
        method: 'POST'
      });
      if (!response.ok) throw new Error('Failed to update preference');
      // Show success feedback
    } catch (err) {
      console.error('Error updating preference:', err);
    }
  };

  // Pay Ready Agent Functions
  const analyzeApartment = async () => {
    setLoading(true);
    setError(null);
    try {
      const listingData = {
        ...apartmentData,
        price: parseFloat(apartmentData.price),
        bedrooms: parseInt(apartmentData.bedrooms),
        bathrooms: parseFloat(apartmentData.bathrooms),
        sqft: parseInt(apartmentData.sqft),
        amenities: apartmentData.amenities.split(',').map(a => a.trim()),
        smart_home_features: apartmentData.smart_home_features.split(',').map(f => f.trim())
      };

      const response = await fetch('/api/orchestration/payready/analyze', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ listing_data: listingData })
      });
      
      if (!response.ok) throw new Error('Analysis failed');
      const result = await response.json();
      setApartmentResult(result);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  // Paragon Medical Agent Functions
  const searchClinicalTrials = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch('/api/orchestration/paragon/search-trials', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          conditions: medicalConditions.split(',').map(c => c.trim()),
          phases: medicalPhases.split(',').map(p => p.trim())
        })
      });
      
      if (!response.ok) throw new Error('Search failed');
      const result = await response.json();
      setMedicalResults(result);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const getAgentIcon = (type: string) => {
    switch (type) {
      case 'personal': return <User className="w-5 h-5" />;
      case 'pay_ready': return <Home className="w-5 h-5" />;
      case 'paragon_medical': return <Heart className="w-5 h-5" />;
      default: return <Brain className="w-5 h-5" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active': return 'bg-green-500';
      case 'idle': return 'bg-gray-500';
      case 'error': return 'bg-red-500';
      default: return 'bg-yellow-500';
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-3xl font-bold tracking-tight">Specialized AI Agents</h2>
        <div className="flex items-center space-x-2">
          {Object.values(agents).map((agent) => (
            <div key={agent.id} className="flex items-center space-x-1">
              <div className={`w-2 h-2 rounded-full ${getStatusColor(agent.status)}`} />
              <span className="text-sm">{agent.name}</span>
            </div>
          ))}
        </div>
      </div>

      {error && (
        <Alert variant="destructive">
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      <Tabs defaultValue="personal" className="space-y-4">
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="personal" className="flex items-center space-x-2">
            <User className="w-4 h-4" />
            <span>Personal Agent</span>
          </TabsTrigger>
          <TabsTrigger value="payready" className="flex items-center space-x-2">
            <Home className="w-4 h-4" />
            <span>Pay Ready Agent</span>
          </TabsTrigger>
          <TabsTrigger value="paragon" className="flex items-center space-x-2">
            <Heart className="w-4 h-4" />
            <span>Paragon Medical</span>
          </TabsTrigger>
        </TabsList>

        <TabsContent value="personal" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Personal Assistant Agent</CardTitle>
              <CardDescription>
                Adaptive search with user preference learning and contextual memory
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="user-id">User ID</Label>
                  <Input
                    id="user-id"
                    value={personalUserId}
                    onChange={(e) => setPersonalUserId(e.target.value)}
                    placeholder="user123"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="personal-query">Search Query</Label>
                  <Input
                    id="personal-query"
                    value={personalQuery}
                    onChange={(e) => setPersonalQuery(e.target.value)}
                    placeholder="Find me the best restaurants nearby..."
                  />
                </div>
              </div>
              
              <Button 
                onClick={executePersonalSearch} 
                disabled={loading || !personalQuery}
                className="w-full"
              >
                {loading ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Searching...
                  </>
                ) : (
                  <>
                    <Search className="mr-2 h-4 w-4" />
                    Execute Search
                  </>
                )}
              </Button>

              {personalResults && (
                <div className="space-y-4 pt-4 border-t">
                  <div className="flex items-center justify-between">
                    <h4 className="font-semibold">Search Results</h4>
                    <Badge variant="outline">
                      {personalResults.results.length} results
                    </Badge>
                  </div>
                  
                  {personalResults.preferences_applied.length > 0 && (
                    <div className="flex items-center space-x-2">
                      <span className="text-sm text-muted-foreground">Preferences applied:</span>
                      {personalResults.preferences_applied.map((pref) => (
                        <Badge key={pref} variant="secondary">{pref}</Badge>
                      ))}
                    </div>
                  )}

                  <div className="space-y-2">
                    {personalResults.results.slice(0, 5).map((result) => (
                      <div key={result.id} className="p-3 border rounded-lg space-y-2">
                        <p className="text-sm">{result.content}</p>
                        <div className="flex items-center justify-between">
                          <Badge variant="outline">
                            Score: {result.final_score.toFixed(2)}
                          </Badge>
                          <div className="flex space-x-2">
                            <Button
                              size="sm"
                              variant="ghost"
                              onClick={() => learnPreference('search_result', 'positive')}
                            >
                              <CheckCircle className="w-4 h-4 text-green-500" />
                            </Button>
                            <Button
                              size="sm"
                              variant="ghost"
                              onClick={() => learnPreference('search_result', 'negative')}
                            >
                              <XCircle className="w-4 h-4 text-red-500" />
                            </Button>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="payready" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Pay Ready Rental Assistant</CardTitle>
              <CardDescription>
                Apartment analysis with tech amenity scoring and market insights
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="apt-address">Address</Label>
                  <Input
                    id="apt-address"
                    value={apartmentData.address}
                    onChange={(e) => setApartmentData({...apartmentData, address: e.target.value})}
                    placeholder="123 Main St, City, State"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="apt-price">Monthly Rent</Label>
                  <Input
                    id="apt-price"
                    type="number"
                    value={apartmentData.price}
                    onChange={(e) => setApartmentData({...apartmentData, price: e.target.value})}
                    placeholder="2500"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="apt-bedrooms">Bedrooms</Label>
                  <Input
                    id="apt-bedrooms"
                    type="number"
                    value={apartmentData.bedrooms}
                    onChange={(e) => setApartmentData({...apartmentData, bedrooms: e.target.value})}
                    placeholder="2"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="apt-sqft">Square Feet</Label>
                  <Input
                    id="apt-sqft"
                    type="number"
                    value={apartmentData.sqft}
                    onChange={(e) => setApartmentData({...apartmentData, sqft: e.target.value})}
                    placeholder="1200"
                  />
                </div>
              </div>

              <div className="space-y-2">
                <Label htmlFor="apt-amenities">Amenities (comma-separated)</Label>
                <Textarea
                  id="apt-amenities"
                  value={apartmentData.amenities}
                  onChange={(e: React.ChangeEvent<HTMLTextAreaElement>) => setApartmentData({...apartmentData, amenities: e.target.value})}
                  placeholder="Pool, Gym, Parking, Rooftop deck..."
                  rows={2}
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="apt-smart">Smart Home Features (comma-separated)</Label>
                <Textarea
                  id="apt-smart"
                  value={apartmentData.smart_home_features}
                  onChange={(e: React.ChangeEvent<HTMLTextAreaElement>) => setApartmentData({...apartmentData, smart_home_features: e.target.value})}
                  placeholder="Smart locks, Fiber internet, USB outlets, App payments..."
                  rows={2}
                />
              </div>

              <Button 
                onClick={analyzeApartment} 
                disabled={loading || !apartmentData.address || !apartmentData.price}
                className="w-full"
              >
                {loading ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Analyzing...
                  </>
                ) : (
                  <>
                    <TrendingUp className="mr-2 h-4 w-4" />
                    Analyze Listing
                  </>
                )}
              </Button>

              {apartmentResult && (
                <div className="space-y-4 pt-4 border-t">
                  <div className="flex items-center justify-between">
                    <h4 className="font-semibold">Analysis Results</h4>
                    <Badge 
                      variant={apartmentResult.recommendation === 'recommended' ? 'default' : 'secondary'}
                    >
                      {apartmentResult.recommendation.toUpperCase()}
                    </Badge>
                  </div>

                  <div className="grid grid-cols-3 gap-4">
                    {apartmentResult.top_features.map((feature: string, index: number) => (
                      <Card key={index}>
                        <CardContent className="pt-6">
                          <div className="text-2xl font-bold text-center">
                            {feature.split(':')[1]}
                          </div>
                          <p className="text-xs text-muted-foreground text-center mt-1">
                            {feature.split(':')[0]}
                          </p>
                        </CardContent>
                      </Card>
                    ))}
                  </div>

                  <div className="p-4 bg-muted rounded-lg">
                    <p className="text-sm">
                      <strong>Overall Assessment:</strong> This listing scores {apartmentResult.listing.overall_score.toFixed(1)}/100 
                      based on tech amenities, neighborhood quality, and value for money.
                    </p>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="paragon" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Paragon Medical Research Agent</CardTitle>
              <CardDescription>
                Clinical trial discovery for Stage 3/4 trials in internal medicine
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="conditions">Medical Conditions (comma-separated)</Label>
                <Textarea
                  id="conditions"
                  value={medicalConditions}
                  onChange={(e: React.ChangeEvent<HTMLTextAreaElement>) => setMedicalConditions(e.target.value)}
                  placeholder="Chronic pain, Fibromyalgia, Arthritis..."
                  rows={2}
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="phases">Trial Phases (comma-separated)</Label>
                <Input
                  id="phases"
                  value={medicalPhases}
                  onChange={(e) => setMedicalPhases(e.target.value)}
                  placeholder="Phase 3, Phase 4"
                />
              </div>

              <Button 
                onClick={searchClinicalTrials} 
                disabled={loading || !medicalConditions}
                className="w-full"
              >
                {loading ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Searching Trials...
                  </>
                ) : (
                  <>
                    <Activity className="mr-2 h-4 w-4" />
                    Search Clinical Trials
                  </>
                )}
              </Button>

              {medicalResults && (
                <div className="space-y-4 pt-4 border-t">
                  <div className="flex items-center justify-between">
                    <h4 className="font-semibold">Clinical Trials Found</h4>
                    <Badge variant="outline">
                      {medicalResults.total_found} trials
                    </Badge>
                  </div>

                  <div className="space-y-3">
                    {medicalResults.trials.slice(0, 5).map((trial: ClinicalTrial) => (
                      <Card key={trial.nct_id}>
                        <CardContent className="pt-4">
                          <div className="flex items-start justify-between">
                            <div className="space-y-1 flex-1">
                              <p className="font-medium">{trial.title}</p>
                              <div className="flex items-center space-x-2 text-sm text-muted-foreground">
                                <Badge variant="outline">{trial.nct_id}</Badge>
                                <Badge variant="secondary">{trial.phase}</Badge>
                                <span>Relevance: {trial.relevance_score.toFixed(0)}%</span>
                              </div>
                              <p className="text-sm text-muted-foreground">
                                Conditions: {trial.conditions.join(', ')}
                              </p>
                            </div>
                            {trial.distance_miles && (
                              <div className="flex items-center text-sm text-muted-foreground">
                                <MapPin className="w-4 h-4 mr-1" />
                                {trial.distance_miles.toFixed(1)} miles
                              </div>
                            )}
                          </div>
                        </CardContent>
                      </Card>
                    ))}
                  </div>

                  <Button variant="outline" className="w-full">
                    Set Up Trial Alerts
                  </Button>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};