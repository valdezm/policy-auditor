'use client';

import { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Button } from '@/components/ui/button';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { CheckCircle2, XCircle, AlertCircle, FileText, ArrowLeft, Eye } from 'lucide-react';
import Link from 'next/link';

interface PolicyAnalysis {
  policy_code: string;
  policy_title: string;
  compliance_score: number;
  is_compliant: boolean;
  has_reference: boolean;
  missing_elements: string[];
  found_elements: string[];
  explanation: string;
  recommendations: string[];
  excerpts: Array<{
    text: string;
    context: string;
  }>;
}

interface RequirementAnalysis {
  requirement_id: string;
  apl_code: string;
  apl_title: string;
  section_code: string;
  requirement_text: string;
  validation_rule: string;
  total_policies_analyzed: number;
  compliant_policies: number;
  analyses: PolicyAnalysis[];
}

interface PolicyDetails {
  policy_id: string;
  policy_code: string;
  title: string;
  filename: string;
  extracted_text: string;
  file_size: number;
}

export default function RequirementDetailPage() {
  const params = useParams();
  const requirementId = params.id as string;
  const [analysis, setAnalysis] = useState<RequirementAnalysis | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedPolicy, setSelectedPolicy] = useState<PolicyDetails | null>(null);
  const [policyModalOpen, setPolicyModalOpen] = useState(false);
  const [filterType, setFilterType] = useState<string>('all');

  useEffect(() => {
    if (requirementId) {
      fetchAnalysis();
    }
  }, [requirementId]);

  const fetchAnalysis = async () => {
    try {
      const response = await fetch(`http://localhost:8001/api/v2/requirements/${requirementId}/analysis`);
      if (!response.ok) throw new Error('Failed to fetch analysis');
      const data = await response.json();
      setAnalysis(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load analysis');
    } finally {
      setLoading(false);
    }
  };

  const cleanPolicyTitle = (title: string, code: string) => {
    // If title looks like a filename, just use the policy code
    if (title.includes('.pdf') || title.includes('_CEO') || title.includes('_v20')) {
      return code;
    }
    return title;
  };

  const fetchPolicyDetails = async (policyCode: string) => {
    try {
      // First find the policy ID from the analysis
      const policy = analysis?.analyses.find(a => a.policy_code === policyCode);
      if (!policy) return;
      
      // For now, create a mock policy ID - we'll need to get this from the backend
      const mockPolicyId = '6f3f30bc-cbae-45e1-966b-b139bbdddb11'; // This should come from the analysis data
      
      const response = await fetch(`http://localhost:8001/api/v2/policies/${mockPolicyId}`);
      if (!response.ok) throw new Error('Failed to fetch policy details');
      
      const data = await response.json();
      setSelectedPolicy(data);
      setPolicyModalOpen(true);
    } catch (err) {
      console.error('Error fetching policy details:', err);
    }
  };

  const getComplianceIcon = (isCompliant: boolean, hasReference: boolean) => {
    if (isCompliant) return <CheckCircle2 className="w-5 h-5 text-green-600" />;
    if (hasReference) return <AlertCircle className="w-5 h-5 text-yellow-600" />;
    return <XCircle className="w-5 h-5 text-red-600" />;
  };

  const getComplianceBadge = (score: number) => {
    if (score >= 0.8) return <Badge className="bg-green-100 text-green-800">Compliant</Badge>;
    if (score >= 0.5) return <Badge className="bg-yellow-100 text-yellow-800">Partial</Badge>;
    if (score > 0) return <Badge className="bg-orange-100 text-orange-800">Minimal</Badge>;
    return <Badge className="bg-red-100 text-red-800">Non-compliant</Badge>;
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-lg">Loading analysis...</div>
      </div>
    );
  }

  if (error || !analysis) {
    return (
      <div className="min-h-screen p-8">
        <Alert variant="destructive">
          <AlertDescription>{error || 'No analysis available'}</AlertDescription>
        </Alert>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-6">
          <Link href="/requirements" className="flex items-center text-blue-600 hover:text-blue-800 mb-4">
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back to Requirements
          </Link>
          <h1 className="text-3xl font-bold">{analysis.apl_code} - {analysis.section_code}</h1>
          <h2 className="text-xl text-gray-700 mt-2 mb-4">{analysis.apl_title}</h2>
          <div className="bg-blue-50 border-l-4 border-blue-400 p-4 mb-4">
            <p className="text-gray-800">{analysis.requirement_text}</p>
          </div>
          <p className="text-gray-600">
            Analyzed {analysis.total_policies_analyzed} policies • 
            {analysis.compliant_policies} compliant
          </p>
        </div>

        {/* Summary Card */}
        <Card className="mb-6">
          <CardHeader>
            <CardTitle>Compliance Summary</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-4 gap-4">
              <div 
                className={`text-center cursor-pointer hover:bg-green-50 p-2 rounded transition-colors ${filterType === 'compliant' ? 'bg-green-100 ring-2 ring-green-500' : ''}`}
                onClick={() => setFilterType(filterType === 'compliant' ? 'all' : 'compliant')}
              >
                <div className="text-2xl font-bold text-green-600">
                  {analysis.analyses.filter(a => a.is_compliant).length}
                </div>
                <p className="text-sm text-gray-600">Fully Compliant</p>
              </div>
              <div 
                className={`text-center cursor-pointer hover:bg-yellow-50 p-2 rounded transition-colors ${filterType === 'reference' ? 'bg-yellow-100 ring-2 ring-yellow-500' : ''}`}
                onClick={() => setFilterType(filterType === 'reference' ? 'all' : 'reference')}
              >
                <div className="text-2xl font-bold text-yellow-600">
                  {analysis.analyses.filter(a => !a.is_compliant && a.has_reference).length}
                </div>
                <p className="text-sm text-gray-600">References Only</p>
              </div>
              <div 
                className={`text-center cursor-pointer hover:bg-orange-50 p-2 rounded transition-colors ${filterType === 'partial' ? 'bg-orange-100 ring-2 ring-orange-500' : ''}`}
                onClick={() => setFilterType(filterType === 'partial' ? 'all' : 'partial')}
              >
                <div className="text-2xl font-bold text-orange-600">
                  {analysis.analyses.filter(a => !a.is_compliant && !a.has_reference && a.compliance_score > 0).length}
                </div>
                <p className="text-sm text-gray-600">Partial Coverage</p>
              </div>
              <div 
                className={`text-center cursor-pointer hover:bg-red-50 p-2 rounded transition-colors ${filterType === 'none' ? 'bg-red-100 ring-2 ring-red-500' : ''}`}
                onClick={() => setFilterType(filterType === 'none' ? 'all' : 'none')}
              >
                <div className="text-2xl font-bold text-red-600">
                  {analysis.analyses.filter(a => a.compliance_score === 0).length}
                </div>
                <p className="text-sm text-gray-600">No Coverage</p>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Policy Analyses */}
        <div className="space-y-6">
          {analysis.analyses
            .filter((policyAnalysis) => {
              if (filterType === 'all') return true;
              if (filterType === 'compliant') return policyAnalysis.is_compliant;
              if (filterType === 'reference') return !policyAnalysis.is_compliant && policyAnalysis.has_reference;
              if (filterType === 'partial') return !policyAnalysis.is_compliant && !policyAnalysis.has_reference && policyAnalysis.compliance_score > 0;
              if (filterType === 'none') return policyAnalysis.compliance_score === 0;
              return true;
            })
            .map((policyAnalysis) => (
            <Card key={policyAnalysis.policy_code} 
                  className={policyAnalysis.is_compliant ? 'border-green-200' : 
                            policyAnalysis.has_reference ? 'border-yellow-200' : 
                            'border-red-200'}>
              <CardHeader>
                <div className="flex items-start justify-between">
                  <div className="flex items-center gap-3">
                    {getComplianceIcon(policyAnalysis.is_compliant, policyAnalysis.has_reference)}
                    <div>
                      <CardTitle className="text-xl">
                        <Button
                          variant="link"
                          className="p-0 h-auto font-bold text-xl text-left"
                          onClick={() => fetchPolicyDetails(policyAnalysis.policy_code)}
                        >
                          <Eye className="w-4 h-4 mr-2" />
                          {cleanPolicyTitle(policyAnalysis.policy_title, policyAnalysis.policy_code)}
                        </Button>
                      </CardTitle>
                      <CardDescription>
                        Compliance Score: {(policyAnalysis.compliance_score * 100).toFixed(0)}%
                      </CardDescription>
                    </div>
                  </div>
                  {getComplianceBadge(policyAnalysis.compliance_score)}
                </div>
              </CardHeader>
              <CardContent>
                <Tabs defaultValue="explanation" className="w-full">
                  <TabsList>
                    <TabsTrigger value="explanation">Explanation</TabsTrigger>
                    <TabsTrigger value="elements">Elements</TabsTrigger>
                    <TabsTrigger value="excerpts">Excerpts</TabsTrigger>
                    <TabsTrigger value="recommendations">Recommendations</TabsTrigger>
                  </TabsList>

                  <TabsContent value="explanation" className="mt-4">
                    <div className="bg-gray-50 p-4 rounded-lg">
                      <pre className="whitespace-pre-wrap text-sm">{policyAnalysis.explanation}</pre>
                    </div>
                  </TabsContent>

                  <TabsContent value="elements" className="mt-4">
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <h4 className="font-semibold mb-2 flex items-center">
                          <CheckCircle2 className="w-4 h-4 text-green-600 mr-2" />
                          Found Elements ({policyAnalysis.found_elements.length})
                        </h4>
                        <ul className="space-y-1">
                          {policyAnalysis.found_elements.map((element, idx) => (
                            <li key={idx} className="text-sm bg-green-50 p-2 rounded">
                              ✓ {element}
                            </li>
                          ))}
                          {policyAnalysis.found_elements.length === 0 && (
                            <li className="text-sm text-gray-500 italic">None found</li>
                          )}
                        </ul>
                      </div>
                      <div>
                        <h4 className="font-semibold mb-2 flex items-center">
                          <XCircle className="w-4 h-4 text-red-600 mr-2" />
                          Missing Elements ({policyAnalysis.missing_elements.length})
                        </h4>
                        <ul className="space-y-1">
                          {policyAnalysis.missing_elements.map((element, idx) => (
                            <li key={idx} className="text-sm bg-red-50 p-2 rounded">
                              ✗ {element}
                            </li>
                          ))}
                          {policyAnalysis.missing_elements.length === 0 && (
                            <li className="text-sm text-gray-500 italic">All requirements met</li>
                          )}
                        </ul>
                      </div>
                    </div>
                  </TabsContent>

                  <TabsContent value="excerpts" className="mt-4">
                    {policyAnalysis.excerpts.length > 0 ? (
                      <div className="space-y-3">
                        {policyAnalysis.excerpts.map((excerpt, idx) => (
                          <div key={idx} className="bg-gray-50 p-4 rounded-lg">
                            <p className="text-sm font-mono mb-2">Match: &quot;{excerpt.text}&quot;</p>
                            <div className="text-sm text-gray-700 border-l-4 border-blue-400 pl-4">
                              {excerpt.context.split('**').map((part, i) => 
                                i % 2 === 0 ? part : <mark key={i} className="bg-yellow-200">{part}</mark>
                              )}
                            </div>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <p className="text-sm text-gray-500 italic">No relevant excerpts found</p>
                    )}
                  </TabsContent>

                  <TabsContent value="recommendations" className="mt-4">
                    {policyAnalysis.recommendations.length > 0 ? (
                      <ul className="space-y-2">
                        {policyAnalysis.recommendations.map((rec, idx) => (
                          <li key={idx} className="flex items-start">
                            <span className="text-blue-600 mr-2">→</span>
                            <span className="text-sm">{rec}</span>
                          </li>
                        ))}
                      </ul>
                    ) : (
                      <p className="text-sm text-green-600">
                        ✓ No recommendations - policy appears complete for this requirement
                      </p>
                    )}
                  </TabsContent>
                </Tabs>
              </CardContent>
            </Card>
          ))}
        </div>

        {/* Policy Modal */}
        <Dialog open={policyModalOpen} onOpenChange={setPolicyModalOpen}>
          <DialogContent className="max-w-4xl max-h-[80vh] overflow-y-auto">
            <DialogHeader>
              <DialogTitle className="flex items-center gap-2">
                <FileText className="w-5 h-5" />
                Policy: {selectedPolicy?.title || selectedPolicy?.policy_code}
              </DialogTitle>
              <DialogDescription>
                Full policy text ({selectedPolicy?.file_size ? Math.round(selectedPolicy.file_size / 1000) : 0}KB)
              </DialogDescription>
            </DialogHeader>
            
            <div className="mt-4">
              {selectedPolicy ? (
                <div className="bg-gray-50 p-4 rounded-lg border">
                  <div className="mb-4 text-sm text-gray-600">
                    <strong>File:</strong> {selectedPolicy.filename}
                  </div>
                  <div className="whitespace-pre-wrap font-mono text-sm leading-relaxed">
                    {selectedPolicy.extracted_text || 'No text content available.'}
                  </div>
                </div>
              ) : (
                <div className="text-center py-8">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
                  <p className="mt-2 text-gray-600">Loading policy content...</p>
                </div>
              )}
            </div>
          </DialogContent>
        </Dialog>
      </div>
    </div>
  );
}