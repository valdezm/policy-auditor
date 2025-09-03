'use client'

import { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Progress } from "@/components/ui/progress"
import { ScrollArea } from "@/components/ui/scroll-area"
import { 
  CheckCircle2, 
  XCircle, 
  AlertCircle,
  FileText,
  ClipboardList
} from "lucide-react"

interface CoverageData {
  overall_coverage: number
  total_requirements: number
  covered: number
  partial: number
  uncovered: number
  by_rt_apl: Array<{
    apl_code: string
    total: number
    covered: number
    partial: number
    uncovered: number
    requirements: Array<{
      id: string
      text: string
      status: string
      policies: string[]
      confidence: number
    }>
  }>
}

export default function CorpusCoverageView() {
  const [coverageData, setCoverageData] = useState<CoverageData | null>(null)
  const [selectedAPL, setSelectedAPL] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchCoverageData()
  }, [])

  const fetchCoverageData = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/coverage/summary')
      const data = await response.json()
      setCoverageData(data)
      setLoading(false)
    } catch (error) {
      console.error('Failed to fetch coverage data:', error)
      setLoading(false)
    }
  }

  const getStatusIcon = (status: string) => {
    switch(status) {
      case 'covered': return <CheckCircle2 className="w-4 h-4 text-green-500" />
      case 'partial': return <AlertCircle className="w-4 h-4 text-yellow-500" />
      case 'uncovered': return <XCircle className="w-4 h-4 text-red-500" />
      default: return null
    }
  }

  const getStatusColor = (status: string) => {
    switch(status) {
      case 'covered': return 'text-green-600 bg-green-50'
      case 'partial': return 'text-yellow-600 bg-yellow-50'
      case 'uncovered': return 'text-red-600 bg-red-50'
      default: return 'text-gray-600 bg-gray-50'
    }
  }

  if (loading) {
    return <div className="flex justify-center items-center h-64">Loading...</div>
  }

  if (!coverageData) {
    return <div>No coverage data available</div>
  }

  const selectedAPLData = coverageData.by_rt_apl.find(a => a.apl_code === selectedAPL)

  return (
    <div className="p-6 space-y-6">
      {/* Overall Coverage Card */}
      <Card>
        <CardHeader>
          <CardTitle>Corpus Coverage Analysis</CardTitle>
          <CardDescription>
            How well does the entire policy corpus satisfy all review tool requirements?
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div>
              <div className="flex justify-between mb-2">
                <span className="text-2xl font-bold">
                  {coverageData.overall_coverage.toFixed(1)}% Coverage
                </span>
                <span className="text-sm text-gray-500">
                  {coverageData.total_requirements} total requirements
                </span>
              </div>
              <Progress value={coverageData.overall_coverage} className="h-3" />
            </div>
            
            <div className="grid grid-cols-3 gap-4 mt-4">
              <div className="text-center">
                <CheckCircle2 className="w-8 h-8 text-green-500 mx-auto mb-2" />
                <p className="text-2xl font-bold">{coverageData.covered}</p>
                <p className="text-sm text-gray-500">Fully Covered</p>
              </div>
              <div className="text-center">
                <AlertCircle className="w-8 h-8 text-yellow-500 mx-auto mb-2" />
                <p className="text-2xl font-bold">{coverageData.partial}</p>
                <p className="text-sm text-gray-500">Partially Covered</p>
              </div>
              <div className="text-center">
                <XCircle className="w-8 h-8 text-red-500 mx-auto mb-2" />
                <p className="text-2xl font-bold">{coverageData.uncovered}</p>
                <p className="text-sm text-gray-500">Not Covered</p>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* RT APL List */}
        <Card>
          <CardHeader>
            <CardTitle>Review Tools (RT APLs)</CardTitle>
            <CardDescription>Click to see requirement coverage</CardDescription>
          </CardHeader>
          <CardContent>
            <ScrollArea className="h-[500px]">
              <div className="space-y-2">
                {coverageData.by_rt_apl.map((apl) => {
                  const coveragePercent = ((apl.covered + apl.partial * 0.5) / apl.total) * 100
                  
                  return (
                    <div
                      key={apl.apl_code}
                      className={`p-4 border rounded-lg cursor-pointer hover:bg-gray-50 ${
                        selectedAPL === apl.apl_code ? 'border-blue-500 bg-blue-50' : ''
                      }`}
                      onClick={() => setSelectedAPL(apl.apl_code)}
                    >
                      <div className="flex items-center justify-between mb-2">
                        <div className="flex items-center gap-2">
                          <ClipboardList className="w-5 h-5 text-gray-400" />
                          <span className="font-medium">{apl.apl_code}</span>
                        </div>
                        <Badge variant="outline">
                          {coveragePercent.toFixed(0)}%
                        </Badge>
                      </div>
                      
                      <Progress value={coveragePercent} className="h-2 mb-2" />
                      
                      <div className="flex gap-4 text-xs text-gray-500">
                        <span className="flex items-center gap-1">
                          <CheckCircle2 className="w-3 h-3 text-green-500" />
                          {apl.covered}
                        </span>
                        <span className="flex items-center gap-1">
                          <AlertCircle className="w-3 h-3 text-yellow-500" />
                          {apl.partial}
                        </span>
                        <span className="flex items-center gap-1">
                          <XCircle className="w-3 h-3 text-red-500" />
                          {apl.uncovered}
                        </span>
                      </div>
                    </div>
                  )
                })}
              </div>
            </ScrollArea>
          </CardContent>
        </Card>

        {/* Requirements Detail */}
        <Card>
          <CardHeader>
            <CardTitle>
              {selectedAPL ? `Requirements for ${selectedAPL}` : 'Select an RT APL'}
            </CardTitle>
            <CardDescription>
              Shows which policies satisfy each requirement
            </CardDescription>
          </CardHeader>
          <CardContent>
            <ScrollArea className="h-[500px]">
              {selectedAPLData ? (
                <div className="space-y-3">
                  {selectedAPLData.requirements.map((req) => (
                    <div key={req.id} className="border rounded-lg p-3">
                      <div className="flex items-start gap-2">
                        {getStatusIcon(req.status)}
                        <div className="flex-1">
                          <div className="flex items-center justify-between mb-1">
                            <span className="font-medium text-sm">
                              Requirement {req.id}
                            </span>
                            <Badge className={getStatusColor(req.status)}>
                              {req.status}
                            </Badge>
                          </div>
                          
                          <p className="text-sm text-gray-600 mb-2">
                            {req.text}
                          </p>
                          
                          {req.policies.length > 0 ? (
                            <div className="space-y-1">
                              <p className="text-xs font-medium text-gray-500">
                                Covered by policies:
                              </p>
                              <div className="flex flex-wrap gap-1">
                                {req.policies.map((policy, idx) => (
                                  <Badge key={idx} variant="outline" className="text-xs">
                                    <FileText className="w-3 h-3 mr-1" />
                                    {policy}
                                  </Badge>
                                ))}
                              </div>
                            </div>
                          ) : (
                            <p className="text-xs text-red-600">
                              No policies found to cover this requirement
                            </p>
                          )}
                          
                          {req.confidence > 0 && (
                            <div className="mt-2">
                              <span className="text-xs text-gray-400">
                                Confidence: {(req.confidence * 100).toFixed(0)}%
                              </span>
                            </div>
                          )}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center text-gray-500 mt-8">
                  Select an RT APL to view its requirements
                </div>
              )}
            </ScrollArea>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}