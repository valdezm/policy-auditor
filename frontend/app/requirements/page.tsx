'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Checkbox } from '@/components/ui/checkbox';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { 
  Dialog, 
  DialogContent, 
  DialogDescription, 
  DialogHeader, 
  DialogTitle 
} from '@/components/ui/dialog';

interface Requirement {
  requirement_id: string;
  apl_code: string;
  section: string;
  requirement_text?: string;
  text?: string;
  regulation_references: string[];
  key_obligations: string[];
  timeframes: string[];
  coverage_type: string;
  confidence_score: number;
  matching_policies: Array<{
    policy_code: string;
    policy_title: string;
    match_details: {
      regulation_matches?: string[];
      apl_mentioned?: boolean;
      excerpts?: string[];
      timeframe_matches?: string[];
    } | string;
  }>;
  gaps: string[];
  manual_review_needed: boolean;
  is_verified: boolean;
  reviewer_notes?: string;
}

interface DetailedCoverage {
  total_requirements: number;
  coverage_summary: {
    full_compliance: number;
    partial_compliance: number;
    reference_only: number;
    related: number;
    no_coverage: number;
    manual_review_needed: number;
    verified: number;
  };
  assessments: Requirement[];
}

export default function RequirementsDashboard() {
  const [coverage, setCoverage] = useState<DetailedCoverage | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedRequirement, setSelectedRequirement] = useState<Requirement | null>(null);
  const [filterType, setFilterType] = useState<string>('all');
  const [filterAPL, setFilterAPL] = useState<string>('all');
  const [showReviewDialog, setShowReviewDialog] = useState(false);
  const [reviewNotes, setReviewNotes] = useState('');

  useEffect(() => {
    fetchDetailedCoverage();
  }, []); // Only fetch once on mount

  const fetchDetailedCoverage = async () => {
    try {
      setLoading(true);
      const url = 'http://localhost:8001/api/v2/coverage/detailed';
      
      const response = await fetch(url);
      if (!response.ok) throw new Error('Failed to fetch coverage data');
      const data = await response.json();
      setCoverage(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load coverage data');
    } finally {
      setLoading(false);
    }
  };

  const getCoverageColor = (type: string) => {
    const colors: { [key: string]: string } = {
      'full_compliance': 'border-green-500 bg-green-50',
      'partial_compliance': 'border-yellow-500 bg-yellow-50',
      'reference_only': 'border-blue-500 bg-blue-50',
      'related': 'border-purple-500 bg-purple-50',
      'no_coverage': 'border-red-500 bg-red-50',
      'manual_review': 'border-gray-500 bg-gray-50'
    };
    return colors[type] || 'border-gray-300';
  };

  const getCoverageBadge = (type: string) => {
    const badges: { [key: string]: JSX.Element } = {
      'full_compliance': <Badge className="bg-green-100 text-green-800">Full Compliance</Badge>,
      'partial_compliance': <Badge className="bg-yellow-100 text-yellow-800">Partial</Badge>,
      'reference_only': <Badge className="bg-blue-100 text-blue-800">Reference Only</Badge>,
      'related': <Badge className="bg-purple-100 text-purple-800">Related</Badge>,
      'no_coverage': <Badge className="bg-red-100 text-red-800">No Coverage</Badge>,
      'manual_review': <Badge className="bg-gray-100 text-gray-800">Needs Review</Badge>
    };
    return badges[type] || <Badge>Unknown</Badge>;
  };

  const handleVerificationToggle = async (requirement: Requirement, verified: boolean) => {
    // Update verification status
    const response = await fetch(`http://localhost:8001/api/v2/requirements/${requirement.requirement_id}/review`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        requirement_id: requirement.requirement_id,
        coverage_type: verified ? 'full_compliance' : requirement.coverage_type,
        policy_references: requirement.matching_policies.map(p => p.policy_code),
        reviewer_notes: reviewNotes,
        is_verified: verified
      })
    });
    
    if (response.ok) {
      fetchDetailedCoverage(); // Refresh data
      setShowReviewDialog(false);
      setReviewNotes('');
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-lg">Loading requirement coverage data...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen p-8">
        <Alert variant="destructive">
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      </div>
    );
  }

  if (!coverage) return null;

  // Filter assessments based on client-side filters
  const filteredAssessments = coverage.assessments.filter(req => {
    // Filter by coverage type
    if (filterType !== 'all' && req.coverage_type !== filterType) return false;
    
    // Filter by APL code
    if (filterAPL !== 'all' && req.apl_code !== filterAPL) return false;
    
    return true;
  });

  const uniqueAPLs = [...new Set(coverage.assessments.map(a => a.apl_code).filter(Boolean))].sort();

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-full mx-auto">
        <h1 className="text-3xl font-bold mb-8">Detailed Requirement Coverage Analysis</h1>
        
        {/* Summary Stats */}
        <div className="grid grid-cols-1 md:grid-cols-7 gap-4 mb-8">
          <Card 
            className={`cursor-pointer hover:shadow-lg transition-shadow ${filterType === 'all' ? 'ring-2 ring-blue-500' : ''}`}
            onClick={() => {
              setFilterType('all');
              setFilterAPL('all');
            }}
          >
            <CardHeader className="pb-3">
              <CardTitle className="text-sm">Total</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{filteredAssessments.length}</div>
            </CardContent>
          </Card>
          
          <Card 
            className={`border-green-200 cursor-pointer hover:shadow-lg transition-shadow ${filterType === 'full_compliance' ? 'ring-2 ring-green-500' : ''}`}
            onClick={() => setFilterType('full_compliance')}
          >
            <CardHeader className="pb-3">
              <CardTitle className="text-sm">Full Compliance</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-green-600">
                {coverage.coverage_summary.full_compliance}
              </div>
            </CardContent>
          </Card>
          
          <Card 
            className={`border-yellow-200 cursor-pointer hover:shadow-lg transition-shadow ${filterType === 'partial_compliance' ? 'ring-2 ring-yellow-500' : ''}`}
            onClick={() => setFilterType('partial_compliance')}
          >
            <CardHeader className="pb-3">
              <CardTitle className="text-sm">Partial</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-yellow-600">
                {coverage.coverage_summary.partial_compliance}
              </div>
            </CardContent>
          </Card>
          
          <Card 
            className={`border-blue-200 cursor-pointer hover:shadow-lg transition-shadow ${filterType === 'reference_only' ? 'ring-2 ring-blue-500' : ''}`}
            onClick={() => setFilterType('reference_only')}
          >
            <CardHeader className="pb-3">
              <CardTitle className="text-sm">Reference Only</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-blue-600">
                {coverage.coverage_summary.reference_only}
              </div>
            </CardContent>
          </Card>
          
          <Card 
            className={`border-purple-200 cursor-pointer hover:shadow-lg transition-shadow ${filterType === 'related' ? 'ring-2 ring-purple-500' : ''}`}
            onClick={() => setFilterType('related')}
          >
            <CardHeader className="pb-3">
              <CardTitle className="text-sm">Related</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-purple-600">
                {coverage.coverage_summary.related}
              </div>
            </CardContent>
          </Card>
          
          <Card 
            className={`border-red-200 cursor-pointer hover:shadow-lg transition-shadow ${filterType === 'no_coverage' ? 'ring-2 ring-red-500' : ''}`}
            onClick={() => setFilterType('no_coverage')}
          >
            <CardHeader className="pb-3">
              <CardTitle className="text-sm">No Coverage</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-red-600">
                {coverage.coverage_summary.no_coverage}
              </div>
            </CardContent>
          </Card>
          
          <Card className="border-gray-200">
            <CardHeader className="pb-3">
              <CardTitle className="text-sm">Verified</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-gray-600">
                {coverage.coverage_summary.verified}
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Filters */}
        <div className="flex gap-4 mb-6 items-center">
          <div className="flex flex-col">
            <label className="text-sm font-medium mb-1">Coverage Type</label>
            <select 
              className="px-4 py-2 border rounded-lg bg-white shadow-sm focus:ring-2 focus:ring-blue-500"
              value={filterType}
              onChange={(e) => {
                console.log('Filter changed to:', e.target.value);
                setFilterType(e.target.value);
              }}
            >
              <option value="all">All Coverage Types</option>
              <option value="full_compliance">Full Compliance</option>
              <option value="partial_compliance">Partial Compliance</option>
              <option value="reference_only">Reference Only</option>
              <option value="related">Related</option>
              <option value="no_coverage">No Coverage</option>
            </select>
          </div>
          
          <div className="flex flex-col">
            <label className="text-sm font-medium mb-1">APL Code</label>
            <select 
              className="px-4 py-2 border rounded-lg bg-white shadow-sm focus:ring-2 focus:ring-blue-500"
              value={filterAPL}
              onChange={(e) => {
                console.log('APL filter changed to:', e.target.value);
                setFilterAPL(e.target.value);
              }}
            >
              <option value="all">All APLs ({uniqueAPLs.length})</option>
              {uniqueAPLs.map(apl => (
                <option key={apl} value={apl}>{apl}</option>
              ))}
            </select>
          </div>
          
          {(filterType !== 'all' || filterAPL !== 'all') && (
            <div className="flex flex-col justify-end">
              <button
                onClick={() => {
                  setFilterType('all');
                  setFilterAPL('all');
                }}
                className="px-3 py-2 text-sm text-gray-600 hover:text-gray-800 underline"
              >
                Clear Filters
              </button>
            </div>
          )}
        </div>

        {/* Requirements Table */}
        <Card>
          <CardHeader>
            <CardTitle>Requirements Detail</CardTitle>
            <CardDescription>
              Click on a requirement to see full details and matching policies
            </CardDescription>
          </CardHeader>
          <CardContent className="p-0">
            <div className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead className="w-12">✓</TableHead>
                    <TableHead className="w-20">APL</TableHead>
                    <TableHead className="w-20">Section</TableHead>
                    <TableHead className="min-w-[400px] max-w-[500px]">Requirement</TableHead>
                    <TableHead className="w-32">Regulations</TableHead>
                    <TableHead className="w-28">Coverage</TableHead>
                    <TableHead className="w-20">Confidence</TableHead>
                    <TableHead className="w-32">Policies</TableHead>
                    <TableHead className="w-20">Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {filteredAssessments
                    .sort((a, b) => {
                      // First sort by APL code with null safety
                      const aplA = a.apl_code || '';
                      const aplB = b.apl_code || '';
                      const aplComparison = aplA.localeCompare(aplB);
                      if (aplComparison !== 0) return aplComparison;
                      
                      // Then sort by section with null safety
                      const sectionA = a.section || '';
                      const sectionB = b.section || '';
                      return sectionA.localeCompare(sectionB, undefined, {
                        numeric: true,
                        sensitivity: 'base'
                      });
                    })
                    .map((req) => (
                    <TableRow 
                      key={req.requirement_id}
                      className={`hover:bg-gray-50 ${getCoverageColor(req.coverage_type)}`}
                    >
                      <TableCell>
                        <Checkbox 
                          checked={req.is_verified}
                          onCheckedChange={() => {
                            setSelectedRequirement(req);
                            setShowReviewDialog(true);
                          }}
                        />
                      </TableCell>
                      <TableCell className="font-mono text-sm">{req.apl_code}</TableCell>
                      <TableCell className="font-medium">{req.section}</TableCell>
                      <TableCell>
                        <div className="max-w-md">
                          <p className="text-sm break-words" title={req.requirement_text || req.text || 'No description available'}>
                            {req.requirement_text && req.requirement_text.length > 200 ? 
                              req.requirement_text.substring(0, 200) + '...' : 
                              req.requirement_text ||
                              (req.text && req.text.length > 200 ? 
                                req.text.substring(0, 200) + '...' : 
                                req.text) ||
                              'No requirement text available'
                            }
                          </p>
                          {req.timeframes && req.timeframes.length > 0 && (
                            <div className="mt-1">
                              {req.timeframes.map(tf => (
                                <Badge key={tf} variant="outline" className="text-xs mr-1">
                                  {tf}
                                </Badge>
                              ))}
                            </div>
                          )}
                        </div>
                      </TableCell>
                      <TableCell>
                        <div className="flex flex-wrap gap-1">
                          {req.regulation_references.map(reg => (
                            <Badge key={reg} variant="outline" className="text-xs">
                              {reg}
                            </Badge>
                          ))}
                        </div>
                      </TableCell>
                      <TableCell>{getCoverageBadge(req.coverage_type)}</TableCell>
                      <TableCell>
                        <span className="text-sm">
                          {(req.confidence_score * 100).toFixed(0)}%
                        </span>
                      </TableCell>
                      <TableCell>
                        {req.matching_policies.length > 0 ? (
                          <div className="space-y-1">
                            <div className="text-sm font-medium">
                              {req.matching_policies.length} {req.matching_policies.length === 1 ? 'policy' : 'policies'}
                            </div>
                            {req.matching_policies.slice(0, 2).map(p => (
                              <Badge key={p.policy_code} className="text-xs block mb-1 max-w-[120px] truncate" title={p.policy_title}>
                                {p.policy_code}
                              </Badge>
                            ))}
                            {req.matching_policies.length > 2 && (
                              <span className="text-xs text-gray-500">
                                +{req.matching_policies.length - 2} more
                              </span>
                            )}
                          </div>
                        ) : (
                          <span className="text-xs text-gray-500">None</span>
                        )}
                      </TableCell>
                      <TableCell>
                        <Link href={`/requirements/${req.requirement_id}`}>
                          <Button 
                            size="sm" 
                            variant="outline"
                          >
                            Details
                          </Button>
                        </Link>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Detail Dialog */}
      {selectedRequirement && (
        <Dialog open={!!selectedRequirement} onOpenChange={() => setSelectedRequirement(null)}>
          <DialogContent className="max-w-4xl max-h-[80vh] overflow-y-auto">
            <DialogHeader>
              <DialogTitle>
                Requirement {selectedRequirement.apl_code} - {selectedRequirement.section}
              </DialogTitle>
              <DialogDescription>
                {getCoverageBadge(selectedRequirement.coverage_type)}
              </DialogDescription>
            </DialogHeader>
            
            <div className="space-y-4">
              <div>
                <h3 className="font-semibold mb-2">Requirement Text</h3>
                <p className="text-sm bg-gray-50 p-3 rounded">{selectedRequirement.requirement_text}</p>
              </div>
              
              {selectedRequirement.key_obligations.length > 0 && (
                <div>
                  <h3 className="font-semibold mb-2">Key Obligations</h3>
                  <ul className="list-disc pl-5 space-y-1">
                    {selectedRequirement.key_obligations.map((obligation, idx) => (
                      <li key={idx} className="text-sm">{obligation}</li>
                    ))}
                  </ul>
                </div>
              )}
              
              {selectedRequirement.matching_policies.length > 0 && (
                <div>
                  <h3 className="font-semibold mb-2">Matching Policies</h3>
                  <div className="space-y-2">
                    {selectedRequirement.matching_policies.map(policy => (
                      <Card key={policy.policy_code}>
                        <CardHeader className="pb-2">
                          <CardTitle className="text-sm">{policy.policy_code}</CardTitle>
                          <CardDescription className="text-xs">{policy.policy_title}</CardDescription>
                        </CardHeader>
                        <CardContent>
                          <div className="text-xs space-y-1">
                            {typeof policy.match_details === 'object' && policy.match_details?.regulation_matches?.length && policy.match_details.regulation_matches.length > 0 && (
                              <p>✓ Mentions: {policy.match_details.regulation_matches.join(', ')}</p>
                            )}
                            {typeof policy.match_details === 'object' && policy.match_details?.apl_mentioned && (
                              <p>✓ References APL {selectedRequirement.apl_code}</p>
                            )}
                            {typeof policy.match_details === 'object' && policy.match_details?.timeframe_matches?.length && policy.match_details.timeframe_matches.length > 0 && (
                              <p>✓ Timeframes: {policy.match_details.timeframe_matches.join(', ')}</p>
                            )}
                          </div>
                        </CardContent>
                      </Card>
                    ))}
                  </div>
                </div>
              )}
              
              {selectedRequirement.gaps.length > 0 && (
                <div>
                  <h3 className="font-semibold mb-2">Coverage Gaps</h3>
                  <ul className="list-disc pl-5 space-y-1">
                    {selectedRequirement.gaps.map((gap, idx) => (
                      <li key={idx} className="text-sm text-red-600">{gap}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          </DialogContent>
        </Dialog>
      )}

      {/* Review Dialog */}
      {showReviewDialog && selectedRequirement && (
        <Dialog open={showReviewDialog} onOpenChange={setShowReviewDialog}>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Manual Review</DialogTitle>
              <DialogDescription>
                Verify coverage for {selectedRequirement.apl_code} - {selectedRequirement.section}
              </DialogDescription>
            </DialogHeader>
            
            <div className="space-y-4">
              <div>
                <label className="text-sm font-medium">Review Notes</label>
                <Textarea
                  value={reviewNotes}
                  onChange={(e) => setReviewNotes(e.target.value)}
                  placeholder="Add notes about coverage verification..."
                  className="mt-1"
                />
              </div>
              
              <div className="flex gap-2">
                <Button
                  onClick={() => handleVerificationToggle(selectedRequirement, true)}
                  className="bg-green-600"
                >
                  Mark as Verified
                </Button>
                <Button
                  onClick={() => handleVerificationToggle(selectedRequirement, false)}
                  variant="outline"
                >
                  Needs More Work
                </Button>
                <Button
                  onClick={() => setShowReviewDialog(false)}
                  variant="ghost"
                >
                  Cancel
                </Button>
              </div>
            </div>
          </DialogContent>
        </Dialog>
      )}
    </div>
  );
}